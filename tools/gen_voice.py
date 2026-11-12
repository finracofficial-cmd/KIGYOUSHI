#!/usr/bin/env python3
"""Generate narration per segment with ElevenLabs text-to-speech.

Writes episodes/<slug>/assets/narration-raw/<segment-id>.mp3 and skips segments whose audio
already exists and whose text has not changed (a .txt copy of the spoken text sits beside it).
Needs ELEVENLABS_API_KEY. Characters are billed by ElevenLabs; --dry-run prints the count only.

Usage: gen_voice.py <slug> [--only ch01,ch02] [--force] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

from episode_lib import CHANNEL, episode_dir, load_episode, speech_text


def segment_speech(ep: dict, seg: dict, pause: float) -> str:
    readings = ep.get("readings", {})
    lines = [speech_text(line, readings) for b in seg["blocks"] for line in b["lines"]]
    brk = f' <break time="{pause:.1f}s" /> '
    return brk.join(lines)


def tts(text: str, previous: str, following: str, cfg: dict) -> bytes:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set")
    if not cfg.get("voice_id"):
        sys.exit("channel/channel.json narrator.voice_id is empty; choose a voice first")
    body = {"text": text, "model_id": cfg["model_id"], "voice_settings": cfg["voice_settings"]}
    if previous:
        body["previous_text"] = previous
    if following:
        body["next_text"] = following
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}?output_format=mp3_44100_192"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json",
                                          "Accept": "audio/mpeg"})
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
    raise RuntimeError("unreachable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ep = load_episode(a.slug)
    cfg = CHANNEL["narrator"]
    out = episode_dir(a.slug) / "assets" / "narration-raw"
    out.mkdir(parents=True, exist_ok=True)
    segs = ep["segments"]
    only = set(filter(None, a.only.split(",")))
    texts = [segment_speech(ep, s, cfg["line_break_seconds"]) for s in segs]
    total = 0
    for i, seg in enumerate(segs):
        sid = seg["id"]
        if only and sid not in only:
            continue
        mp3, txt = out / f"{sid}.mp3", out / f"{sid}.txt"
        text = texts[i]
        if not a.force and mp3.exists() and txt.exists() and txt.read_text(encoding="utf-8") == text:
            print(f"{sid}: unchanged, skipped")
            continue
        total += len(text)
        if a.dry_run:
            print(f"{sid}: {len(text)} chars")
            continue
        prev = texts[i - 1][-300:] if i > 0 else ""
        nxt = texts[i + 1][:300] if i + 1 < len(texts) else ""
        audio = tts(text, prev, nxt, cfg)
        mp3.write_bytes(audio)
        txt.write_text(text, encoding="utf-8")
        print(f"{sid}: {len(text)} chars -> {mp3.relative_to(episode_dir(a.slug))}")
    print(f"total characters {'to send' if a.dry_run else 'sent'}: {total}")


if __name__ == "__main__":
    main()
