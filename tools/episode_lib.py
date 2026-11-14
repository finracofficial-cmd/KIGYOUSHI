"""Shared helpers for the 栄枯盛衰ファイル episode pipeline.

An episode lives in episodes/<slug>/ and is described by episode.json (see docs/EPISODE_FORMAT.md).
Narration lines may contain inline readings written as [表示|よみ]; the display side is shown in
captions and the reading is what the narrator speaks. episode.json "readings" adds readings for
recurring names automatically.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANNEL = json.loads((ROOT / "channel" / "channel.json").read_text(encoding="utf-8"))

INLINE = re.compile(r"\[([^\[\]|]+)\|([^\[\]|]+)\]")
SCRIPT_RESERVED = re.compile(r"([\\@<>{}|])")


def episode_dir(slug: str) -> Path:
    return ROOT / "episodes" / slug


def load_episode(slug: str) -> dict:
    return json.loads((episode_dir(slug) / "episode.json").read_text(encoding="utf-8"))


def iter_blocks(ep: dict):
    """Yield (segment, block_index, block) for every narration block, merging nothing."""
    for seg in ep["segments"]:
        for i, block in enumerate(seg["blocks"]):
            yield seg, i, block


def tokens(line: str, readings: dict[str, str]):
    """Split a narration line into ("plain", text) and ("dual", display, speech) tokens."""
    out: list[tuple] = []
    pos = 0
    for m in INLINE.finditer(line):
        if m.start() > pos:
            out.extend(_apply_readings(line[pos:m.start()], readings))
        out.append(("dual", m.group(1).strip(), m.group(2).strip()))
        pos = m.end()
    if pos < len(line):
        out.extend(_apply_readings(line[pos:], readings))
    return out


def _apply_readings(text: str, readings: dict[str, str]):
    if not readings:
        return [("plain", text)]
    keys = sorted(readings, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(k) for k in keys))
    out: list[tuple] = []
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            out.append(("plain", text[pos:m.start()]))
        out.append(("dual", m.group(0), readings[m.group(0)]))
        pos = m.end()
    if pos < len(text):
        out.append(("plain", text[pos:]))
    return out


def display_text(line: str) -> str:
    return INLINE.sub(lambda m: m.group(1), line)


def speech_text(line: str, readings: dict[str, str]) -> str:
    return "".join(t[1] if t[0] == "plain" else t[2] for t in tokens(line, readings))


OPENING = set("「『（(〈《【“‘")


def script_prose(line: str, readings: dict[str, str]) -> str:
    """Render one line as Hypit Script prose (Dual Text for readings, reserved chars escaped).

    Hypit attaches unspoken punctuation to the word before it, so an opening bracket would end up at the
    end of the previous caption (or line). Each opening bracket is therefore bound to the next spoken
    character or reading as Dual Text: 「東芝」 → <「東芝|とうしば>」, 「からくり → <「か|か>らくり."""
    esc = lambda s: SCRIPT_RESERVED.sub(r"\\\1", xml_text(s))
    parts, pending = [], ""
    for t in tokens(line, readings):
        if t[0] == "plain":
            for ch in t[1]:
                if ch in OPENING:
                    pending += ch
                elif pending:
                    parts.append(f"<{esc(pending + ch)}|{esc(ch)}>")
                    pending = ""
                else:
                    parts.append(esc(ch))
        else:
            parts.append(f"<{esc(pending + t[1])}|{esc(t[2])}>")
            pending = ""
    return "".join(parts) + esc(pending)


def xml_text(s: str) -> str:
    return s.replace("&", "＆")


def xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


UNREAD = re.compile(r"[0-9０-９A-Za-zＡ-Ｚａ-ｚ]")


def lint_episode(ep: dict) -> list[str]:
    """Return problems that would make narration or captions go wrong."""
    problems: list[str] = []
    readings = ep.get("readings", {})
    images = ep.get("images", {})
    seg_ids = set()
    for seg in ep["segments"]:
        sid = seg["id"]
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", sid) or sid == "script":
            problems.append(f"segment id '{sid}' must match [a-z][a-z0-9_-]*")
        if sid in seg_ids:
            problems.append(f"duplicate segment id '{sid}'")
        seg_ids.add(sid)
        if seg.get("kind") == "chapter" and not seg.get("title"):
            problems.append(f"{sid}: chapter needs a title")
        if not seg.get("blocks"):
            problems.append(f"{sid}: no blocks")
        for i, block in enumerate(seg.get("blocks", [])):
            if block.get("image") not in images:
                problems.append(f"{sid} block {i}: image '{block.get('image')}' is not defined in images")
            for line in block.get("lines", []):
                plain = "".join(t[1] for t in tokens(line, readings) if t[0] == "plain")
                if UNREAD.search(plain):
                    problems.append(f"{sid} block {i}: give a reading for digits/Latin letters: {line}")
                if len(display_text(line)) > 64:
                    problems.append(f"{sid} block {i}: caption over 64 chars, split it: {line}")
    for key in ("credits",):
        if key in ep and ep[key].get("image") not in images:
            problems.append(f"{key}: image '{ep[key].get('image')}' is not defined in images")
    return problems


def credits_duration(ep: dict) -> int:
    """Seconds of the closing source-list roll (0 when the episode has no credits)."""
    credits = ep.get("credits")
    if not credits:
        return 0
    return max(20, round((len(credits.get("sources", [])) + 8) * 1.1))


def planned_seconds(ep: dict, narration_seconds: dict[str, float]) -> float:
    """Film length implied by the episode structure and measured narration durations."""
    tm = CHANNEL["timing"]
    total = sum(narration_seconds.values())
    if any(s.get("kind") == "opening" for s in ep["segments"]):
        total += 0.8
    chapters = [s for s in ep["segments"] if s.get("kind") == "chapter"]
    total += tm["ident_seconds"] + len(chapters) * (tm["card_seconds"] + tm["chapter_tail_seconds"])
    total += credits_duration(ep) + tm["end_card_seconds"]
    return total
