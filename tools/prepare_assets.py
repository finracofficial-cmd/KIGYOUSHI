#!/usr/bin/env python3
"""Prepare derived assets after images and narration exist.

- assets/narration/<seg>.m4a : narration loudness-normalized (channel audio.narration_lufs)
- assets/derived/ident.png   : desaturated, darkened title-card background
- assets/derived/credits.png : darkened background for the source roll
- assets/derived/bgm-bed.m4a : background music looped to the film length at audio.bgm_lufs

Background music comes from episode.json "bgm" or channel/bgm/*.{mp3,m4a,wav} (first file).
Without any music file a near-silent bed is written so the film still builds.

Usage: prepare_assets.py <slug>
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

from episode_lib import CHANNEL, ROOT, episode_dir, load_episode, planned_seconds


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    ep = load_episode(slug)
    d = episode_dir(slug)
    a = d / "assets"
    (a / "narration").mkdir(parents=True, exist_ok=True)
    (a / "derived").mkdir(parents=True, exist_ok=True)
    au = CHANNEL["audio"]

    secs = {}
    for seg in ep["segments"]:
        sid = seg["id"]
        raw = next((p for p in [a / "narration-raw" / f"{sid}.mp3", a / "narration-raw" / f"{sid}.m4a",
                                a / "narration-raw" / f"{sid}.wav"] if p.exists()), None)
        if raw is None:
            sys.exit(f"missing narration for segment {sid} (run gen_voice.py)")
        dst = a / "narration" / f"{sid}.m4a"
        if not dst.exists() or dst.stat().st_mtime < raw.stat().st_mtime:
            run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                 f"loudnorm=I={au['narration_lufs']}:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1",
                 "-c:a", "aac", "-b:a", "160k", str(dst)])
        secs[sid] = duration(dst)

    def bg(src_id: str, dst: Path, saturation: float, brightness: float):
        src = a / "images" / f"{src_id}.png"
        im = Image.open(src).convert("RGB")
        im = ImageEnhance.Color(im).enhance(saturation)
        im = ImageEnhance.Brightness(im).enhance(brightness)
        im.save(dst)

    first_image = ep["segments"][0]["blocks"][0]["image"]
    bg(ep.get("ident_image", first_image), a / "derived" / "ident.png", 0.0, 0.55)
    if ep.get("credits"):
        bg(ep["credits"]["image"], a / "derived" / "credits.png", 0.6, 0.38)

    total = planned_seconds(ep, secs) + 5
    music = ep.get("bgm")
    src = (d / music) if music else next(iter(sorted(
        p for p in (ROOT / "channel" / "bgm").glob("*") if p.suffix.lower() in (".mp3", ".m4a", ".wav"))), None)
    bed = a / "derived" / "bgm-bed.m4a"
    if src and Path(src).exists():
        run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", str(src), "-t", f"{total:.2f}",
             "-af", f"loudnorm=I={au['bgm_lufs']}:TP=-6:LRA=7", "-ar", "48000", "-ac", "2",
             "-c:a", "aac", "-b:a", "160k", str(bed)])
    else:
        print("no background music found in channel/bgm/; writing a silent bed")
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", f"{total:.2f}",
             "-c:a", "aac", "-b:a", "96k", str(bed)])
    print(f"narration {sum(secs.values()):.1f}s, planned film {total - 5:.1f}s")


if __name__ == "__main__":
    main()
