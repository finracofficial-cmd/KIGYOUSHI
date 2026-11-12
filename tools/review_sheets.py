#!/usr/bin/env python3
"""Write review contact sheets for a finished video so Claude (or a person) can check it.

- overview-*.jpg : one frame every 10 s, time-labeled, 4x4 per sheet
- loudness.txt   : integrated loudness and true peak of the final mix

Usage: review_sheets.py <video.mp4> <out-dir>
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path(__file__).resolve().parent.parent / "channel" / "fonts" / "NotoSansJP-VariableFont.ttf"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    video, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True, check=True).stdout)
    times = [t for t in range(0, int(dur), 10)]
    cw, chh = 480, 270
    font = ImageFont.truetype(str(FONT), 22)
    per = 16
    for page in range(0, len(times), per):
        sheet = Image.new("RGB", (cw * 4, (chh + 30) * 4), (16, 16, 16))
        dr = ImageDraw.Draw(sheet)
        for k, t in enumerate(times[page:page + per]):
            png = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1",
                                  "-vf", f"scale={cw}:{chh}", "-f", "image2pipe", "-vcodec", "png", "-"],
                                 capture_output=True, check=True).stdout
            from io import BytesIO
            im = Image.open(BytesIO(png))
            x, y = (k % 4) * cw, (k // 4) * (chh + 30)
            sheet.paste(im, (x, y))
            dr.text((x + 6, y + chh + 2), f"{t // 60:02d}:{t % 60:02d}", font=font, fill=(230, 230, 230))
        sheet.save(out / f"overview-{page // per + 1:02d}.jpg", quality=85)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    summary = r.stderr[r.stderr.rfind("Summary:"):]
    (out / "loudness.txt").write_text(summary, encoding="utf-8")
    print(f"{len(times)} frames on {(len(times) + per - 1) // per} sheet(s); loudness in {out / 'loudness.txt'}")


if __name__ == "__main__":
    main()
