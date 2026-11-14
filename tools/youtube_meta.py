#!/usr/bin/env python3
"""Write out/youtube.txt: title, the full description, and tags.

The description follows a fixed structure:
  overview of the subject and its peak -> the decline with years -> two "なぜ" questions ->
  「今回の栄枯盛衰ファイルでは、〜」 -> invitation to share memories -> 【目次】 chapter timestamps ->
  【栄枯盛衰ファイルについて】 (channel/channel.json youtube.about) ->
  【参考文献・出典について】 summary, main sources, notes, AI notice -> 【参考文献】 list ->
  【主な出典URL】 -> hashtags (channel hashtag first, at most 15).
Episode-specific text comes from episode.json "description" (see docs/EPISODE_FORMAT.md).
Chapter times follow the generated Timeline, measured from the prepared narration files.

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


def chapter_marks(ep: dict, d) -> list[tuple[float, str]]:
    tm = CHANNEL["timing"]
    t = 0.0
    marks = [(0.0, "オープニング")]
    for seg in ep["segments"]:
        dur = duration(d / "assets" / "narration" / f"{seg['id']}.m4a")
        if seg.get("kind") == "opening":
            t += dur + 0.8 + tm["ident_seconds"]
        elif seg.get("kind") == "chapter":
            if t > 0:
                marks.append((t, seg["title"]))
            else:
                marks[0] = (0.0, seg["title"])
            t += tm["card_seconds"] + dur + tm["chapter_tail_seconds"]
        else:
            t += dur
    if ep.get("credits"):
        marks.append((t, "参考資料"))
    return marks


def build_description(ep: dict, marks: list[tuple[float, str]], with_urls: int | None = None) -> str:
    yt = CHANNEL["youtube"]
    desc = ep.get("description")
    blocks: list[str] = []
    if desc:
        blocks.append("\n".join(desc.get("intro", [])))
        tail = list(desc.get("questions", []))
        if desc.get("overview"):
            tail.append(desc["overview"])
        if desc.get("comment_prompt"):
            tail.append(desc["comment_prompt"])
        blocks.append("\n".join(tail))
    else:
        blocks.append(ep.get("youtube_description", "").strip())

    blocks.append("【目次】\n" + "\n".join(f"{stamp(s)} {name}" for s, name in marks))

    about = list(yt["about"])
    if yt.get("url"):
        about.append(yt["url"])
    blocks.append(f"【{CHANNEL['name']}について】\n" + "\n".join(about))

    if desc:
        src = [desc.get("sources_summary", "")]
        if desc.get("main_sources"):
            src.append("主な参考資料：" + "、".join(desc["main_sources"]) + " ほか。")
        src.append("詳しい出典・参考資料は動画末尾のエンドロールにも掲載しています。")
        src += desc.get("notes", [])
        src.append(yt["ai_notice"])
        blocks.append("【参考文献・出典について】\n" + "\n".join(x for x in src if x))
    credits = (ep.get("credits") or {}).get("sources", [])
    if credits:
        blocks.append("【参考文献】\n" + "\n".join(f"・{s}" for s in credits))
    urls = (desc or {}).get("reference_urls", [])
    if with_urls is not None:
        urls = urls[:with_urls]
    if urls:
        blocks.append("【主な出典URL】\n" + "\n".join(f"・{u['title']}\n{u['url']}" for u in urls))

    tags = [yt["hashtag"]] + [h for h in (desc or {}).get("hashtags", []) if h != yt["hashtag"]]
    tags = tags[: yt.get("max_hashtags", 15)]
    blocks.append(" ".join("#" + t.replace(" ", "") for t in tags))
    return "\n\n".join(b for b in blocks if b.strip())


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    ep = load_episode(slug)
    d = episode_dir(slug)
    marks = chapter_marks(ep, d)
    limit = CHANNEL["youtube"].get("max_description_chars", 5000)
    urls = len((ep.get("description") or {}).get("reference_urls", []))
    text = build_description(ep, marks)
    while len(text) > limit and urls > 0:  # drop URLs from the end until it fits YouTube's limit
        urls -= 1
        text = build_description(ep, marks, with_urls=urls)
    for bad in "<>":
        text = text.replace(bad, "")
    if len(text) > limit:
        print(f"warning: description is {len(text)} characters (YouTube allows {limit})")
    out = d / "out"
    out.mkdir(exist_ok=True)
    (out / "description.txt").write_text(text + "\n", encoding="utf-8")
    full = (f"【タイトル】\n{ep.get('youtube_title', '')}\n\n【概要欄】（{len(text)}字）\n{text}\n\n"
            f"【タグ】\n{','.join(ep.get('tags', []))}\n")
    (out / "youtube.txt").write_text(full, encoding="utf-8")
    print(out / "youtube.txt", f"description {len(text)} chars")


if __name__ == "__main__":
    main()
