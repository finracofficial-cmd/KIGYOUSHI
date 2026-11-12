#!/usr/bin/env python3
"""Generate narration with ElevenLabs, one picture block at a time, and check every block's Japanese.

For each block (the lines shown over one picture):
  1. build the spoken text (explicit readings + channel/yomi.json; kana conversion when
     channel narrator.text_mode is "kana"),
  2. synthesize it with ElevenLabs,
  3. transcribe it back with the local WhisperX and compare readings with the script;
     regenerate up to --retries times when the reading error rate exceeds --max-cer
     (a block that stays over the limit is listed in the report for a reading fix).
Blocks are joined with short pauses into assets/narration-raw/<segment>.wav.
A report of every block (error rate, remaining differences) goes to out/voice-report.md.

Unchanged blocks (same text, voice, model) are reused. Needs ELEVENLABS_API_KEY and a running
WhisperX (`hypit programs up --endpoint whisperx.local`). ElevenLabs bills characters per request.

Usage: gen_voice.py <slug> [--only ch01,ch02] [--force] [--dry-run] [--no-check] [--recheck]
                     [--max-cer 0.05] [--retries 1]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from episode_lib import CHANNEL, ROOT, episode_dir, load_episode
from yomi import cer, diff_words, kana_key, speech_for

KANJI_DIGITS = "〇一二三四五六七八九"


def int_to_kanji(n: int) -> str:
    if n == 0:
        return "零"
    units = [(10 ** 12, "兆"), (10 ** 8, "億"), (10 ** 4, "万"), (1, "")]
    out = ""
    for value, name in units:
        part, n = divmod(n, value)
        if part:
            out += _under_10000(part) + name
    return out


def _under_10000(n: int) -> str:
    s = ""
    for value, name in [(1000, "千"), (100, "百"), (10, "十")]:
        d, n = divmod(n, value)
        if d:
            s += ("" if d == 1 else KANJI_DIGITS[d]) + name
    if n:
        s += KANJI_DIGITS[n]
    return s


DIGIT_KANA = "ゼロ イチ ニ サン ヨン ゴ ロク ナナ ハチ キュウ".split()
COUNTERS = "年月日円万億兆人台社件本枚個歳%％倍度時分秒期位回キセメグワ"


def normalize_heard(text: str) -> str:
    """Turn digits from the recognizer into readable form so readings can be compared.

    Codes such as 0840 or 724106 are read digit by digit; quantities (1996年, 1,500人) as numbers."""
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)

    def repl(m):
        digits, nxt = m.group(), text[m.end():m.end() + 1]
        if digits.startswith("0") or len(digits) >= 5 or (len(digits) == 4 and nxt not in COUNTERS):
            if not (nxt and nxt in "年万億円"):
                return "".join(DIGIT_KANA[int(c)] for c in digits)
        return int_to_kanji(int(digits))
    return re.sub(r"\d+", repl, text)


def block_speech(ep, block, mode):
    readings = ep.get("readings", {})
    return [speech_for(line, readings, mode) for line in block["lines"]]


def tts(text: str, cfg: dict, previous: str = "", following: str = "") -> bytes:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set")
    if not cfg.get("voice_id"):
        sys.exit("channel/channel.json narrator.voice_id is empty; choose a voice first")
    model = cfg["model_id"]
    body = {"text": text, "model_id": model, "voice_settings": cfg["voice_settings"]}
    if cfg.get("language_code"):
        body["language_code"] = cfg["language_code"]
    if model != "eleven_v3":  # request stitching is not available on v3
        if previous:
            body["previous_text"] = previous
        if following:
            body["next_text"] = following
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}?output_format=mp3_44100_192"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:400]
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            sys.exit(f"ElevenLabs HTTP {e.code}: {msg}")
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            if attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"network error: {e}")
    raise RuntimeError("unreachable")


def ensure_whisperx():
    try:
        urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=5).read()
    except Exception:
        subprocess.run(["hypit", "programs", "up", "--endpoint", "whisperx.local"], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)


def heard(mp3: Path) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "t.json"
        r = subprocess.run(["hypit", "transcribe", str(mp3), "--language", "ja", "--to", str(out)],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"transcribe failed: {r.stderr.strip()[-300:]}")
        data = json.loads(out.read_text())
    return "".join(p["text"] for p in data["passages"]).replace(" ", "")


def score(expected_lines: list[str], ep: dict, heard_text: str) -> tuple[float, list[str]]:
    # Reference reading: the script with all explicit readings applied, as katakana.
    ref = "".join(speech_for(line, ep.get("readings", {}), "kanji") for line in expected_lines)
    # Apply the same reading dictionary to what was heard, so a correct reading that the
    # recognizer spelled in kanji (e.g. いつの間にか) is not counted as an error.
    hyp = speech_for(normalize_heard(heard_text), ep.get("readings", {}), "kanji")
    return cer(kana_key(ref), kana_key(hyp)), diff_words(ref, hyp)


def concat(parts: list[Path], gap: float, dst: Path):
    inputs, filters = [], []
    for i, p in enumerate(parts):
        inputs += ["-i", str(p)]
    n = len(parts)
    inputs += ["-f", "lavfi", "-t", f"{gap}", "-i", "anullsrc=r=44100:cl=mono"]
    seq = []
    for i in range(n):
        filters.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=mono[a{i}]")
        seq.append(f"[a{i}]")
        if i < n - 1:
            seq.append(f"[{n}:a]")
    graph = ";".join(filters) + ";" + "".join(seq) + f"concat=n={len(seq)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[out]",
                    "-c:a", "pcm_s16le", str(dst)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--max-cer", type=float, default=0.05)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--recheck", action="store_true",
                    help="re-score existing blocks that are over the limit before regenerating them")
    a = ap.parse_args()

    ep = load_episode(a.slug)
    cfg = CHANNEL["narrator"]
    mode = cfg.get("text_mode", "kanji")
    d = episode_dir(a.slug)
    blocks_dir = d / "assets" / "narration-blocks"
    raw_dir = d / "assets" / "narration-raw"
    blocks_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    only = set(filter(None, a.only.split(",")))
    pause = cfg.get("line_break_seconds", 0.6)
    block_gap = cfg.get("block_gap_seconds", 0.8)

    plan = []  # (seg, bi, block, speech_text)
    for seg in ep["segments"]:
        for bi, block in enumerate(seg["blocks"]):
            lines = block_speech(ep, block, mode)
            sep = f' <break time="{pause:.1f}s" /> ' if cfg["model_id"] != "eleven_v3" else "\n"
            plan.append((seg, bi, block, sep.join(lines)))

    total_chars, report = 0, []
    if not a.dry_run and not a.no_check:
        ensure_whisperx()
    for idx, (seg, bi, block, text) in enumerate(plan):
        sid = seg["id"]
        if only and sid not in only:
            continue
        stem = blocks_dir / f"{sid}-{bi:02d}"
        meta_p, mp3 = stem.with_suffix(".json"), stem.with_suffix(".mp3")
        key = {"text": text, "voice": cfg["voice_id"], "model": cfg["model_id"],
               "settings": cfg["voice_settings"], "lang": cfg.get("language_code")}
        meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
        if not a.force and mp3.exists() and meta.get("key") == key:
            if a.recheck and not a.no_check and (meta.get("cer") or 0) > a.max_cer:
                c, diffs = score(block["lines"], ep, heard(mp3))
                meta.update({"cer": round(c, 4), "diff": diffs})
                meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"{sid}-{bi:02d} rechecked: reading error {c:.3f}")
            if (meta.get("cer") or 0) <= a.max_cer or not a.recheck:
                report.append((sid, bi, meta.get("cer"), meta.get("diff", []), "reused"))
                continue
        total_chars += len(text)
        if a.dry_run:
            print(f"{sid}-{bi:02d}: {len(text)} chars")
            continue
        prev = plan[idx - 1][3][-200:] if idx > 0 else ""
        nxt = plan[idx + 1][3][:200] if idx + 1 < len(plan) else ""
        best = None
        for attempt in range(a.retries + 1):
            audio = tts(text, cfg, prev, nxt)
            cand = stem.with_name(stem.name + f".try{attempt}.mp3")
            cand.write_bytes(audio)
            if a.no_check:
                best = (0.0, [], cand)
                break
            c, diffs = score(block["lines"], ep, heard(cand))
            print(f"{sid}-{bi:02d} try {attempt + 1}: reading error {c:.3f}")
            if best is None or c < best[0]:
                best = (c, diffs, cand)
            if c <= a.max_cer:
                break
            total_chars += len(text)
        c, diffs, cand = best
        cand.replace(mp3)
        for leftover in blocks_dir.glob(stem.name + ".try*.mp3"):
            leftover.unlink()
        meta = {"key": key, "cer": round(c, 4), "diff": diffs}
        meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        report.append((sid, bi, c, diffs, "new"))

    if a.dry_run:
        print(f"total characters to send: {total_chars}")
        return

    for seg in ep["segments"]:
        sid = seg["id"]
        if only and sid not in only:
            continue
        parts = [blocks_dir / f"{sid}-{bi:02d}.mp3" for bi in range(len(seg["blocks"]))]
        dst = raw_dir / f"{sid}.wav"
        concat(parts, block_gap, dst)
        for stale in (raw_dir / f"{sid}.mp3", raw_dir / f"{sid}.m4a"):
            stale.unlink(missing_ok=True)

    out = d / "out"
    out.mkdir(exist_ok=True)
    lines = [f"# ナレーション読みチェック（{a.slug}）", "",
             f"モデル {cfg['model_id']} / 読みモード {mode} / 合格ライン 読み誤り率 {a.max_cer:.0%} 以下", "",
             "| ブロック | 読み誤り率 | 状態 | 気になる箇所（台本 → 聞こえた読み） |", "| --- | --- | --- | --- |"]
    bad = 0
    for sid, bi, c, diffs, state in report:
        flag = "" if c is None or c <= a.max_cer else " ⚠"
        bad += bool(flag)
        lines.append(f"| {sid}-{bi:02d} | {'' if c is None else f'{c:.1%}'}{flag} | {state} | {' / '.join(diffs[:3])} |")
    (out / "voice-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"characters sent: {total_chars}; blocks over the limit: {bad}; report: {out / 'voice-report.md'}")


if __name__ == "__main__":
    main()
