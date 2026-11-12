#!/usr/bin/env python3
"""Write out/youtube.txt: title, description with chapter timestamps, and tags.

Chapter times follow the same structure as the generated Timeline (opening, title card,
chapter cards, narration, tails), measured from the prepared narration files.

Usage: youtube_meta.py <slug>
"""
from __future__ import annotations

import subprocess
import sys

from episode_lib import CHANNEL, episode_dir, load_episode


def duration(p) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(p)], capture_output=True, text=True, check=True).stdout)


def stamp(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    ep = load_episode(slug)
    d = episode_dir(slug)
    tm = CHANNEL["timing"]
    t = 0.0
    marks = [(0.0, "オープニング")]
    for seg in ep["segments"]:
        dur = duration(d / "assets" / "narration" / f"{seg['id']}.m4a")
        if seg.get("kind") == "opening":
            t += dur + 0.8 + tm["ident_seconds"]
        else:
            if seg.get("kind") == "chapter":
                if t > 0:
                    marks.append((t, seg["title"]))
                else:
                    marks[0] = (0.0, seg["title"])
                t += tm["card_seconds"] + dur + tm["chapter_tail_seconds"]
            else:
                t += dur
    if ep.get("credits"):
        marks.append((t, "参考資料"))
    chapters = "\n".join(f"{stamp(s)} {name}" for s, name in marks)
    desc = ep.get("youtube_description", "").strip()
    text = (f"【タイトル】\n{ep.get('youtube_title', '')}\n\n【概要欄】\n{desc}\n\n{chapters}\n\n"
            f"#{CHANNEL['name']}\n\n【タグ】\n{', '.join(ep.get('tags', []))}\n")
    out = d / "out"
    out.mkdir(exist_ok=True)
    (out / "youtube.txt").write_text(text, encoding="utf-8")
    print(out / "youtube.txt")


if __name__ == "__main__":
    main()
