#!/usr/bin/env python3
"""Make vertical YouTube Shorts (1080x1920, under 60 s) from an episode's "shorts" entries.

episode.json:
  "shorts": [{
    "id": "s1",
    "youtube_title": "〇〇はなぜ消えた？… #shorts",
    "title": ["〇〇は", "なぜ消えた？"],              # fixed hook at the top (2 lines, the 2nd is gold)
    "scenes": [{"image": "<image id>", "lines": ["字幕1枚＝1文。[数字|よみ] も使える", "..."]}],
    "description": ["説明文", "..."],
    "hashtags": ["〇〇", "企業史"]
  }]

Every line is spoken separately (ElevenLabs, same narrator as the episode) so the caption timing is exact;
the reading is checked by transcribing it back with WhisperX. Pictures come from the episode's images and
slowly zoom; the channel BGM plays underneath. Unchanged lines are not regenerated.

Writes episodes/<slug>/out/shorts/<id>.mp4 and <id>.txt (title, description, hashtags).
Usage: make_shorts.py <slug> [--only s1,s2] [--no-check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from episode_lib import CHANNEL, ROOT, display_text, episode_dir, load_episode
from gen_voice import ensure_whisperx, heard, score, tts
from yomi import speech_for

W, H, FPS = 1080, 1920, 30
PHOTO_Y, PHOTO_H = 560, 720          # picture band
CAP_Y, CAP_W, CAP_SIZE = 1316, 960, 64
TITLE_FONT = ROOT / "channel" / "fonts" / "DelaGothicOne-Regular.ttf"
TEXT_FONT = ROOT / "channel" / "fonts" / "NotoSansJP-VariableFont.ttf"
GOLD = (255, 210, 63)
LEAD, GAP, SCENE_GAP, TAIL = 0.25, 0.2, 0.35, 0.9
NO_LINE_START = set("、。，．・：；？！ー」』）)]’”ぁぃぅぇぉっゃゅょァィゥェォッャュョ")
NO_LINE_END = set("「『（([‘“")


def sh(cmd):
    subprocess.run(cmd, check=True)


def duration(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def font(path: Path, size: int, black: bool = False) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(path), size)
    if black:
        f.set_variation_by_name("Black")
    return f


def _kind(ch: str) -> str:
    if "ぁ" <= ch <= "ゖ":
        return "hira"
    if "ァ" <= ch <= "ヺ" or ch == "ー":
        return "kata"
    if ch.isdigit() or ch in ",.%":
        return "num"
    return "other"


def _good_break(text: str, i: int) -> bool:
    """True when a line may end before text[i]: after punctuation, or where hiragana meets kanji/katakana
    (so words such as トイザらス or 市場 are not split)."""
    a, b = text[i - 1], text[i]
    if b in NO_LINE_START or a in NO_LINE_END:
        return False
    if a in "、。！？」』）":
        return True
    if a in "はがをにでともへ" and i >= 2 and _kind(text[i - 2]) != "hira" and b not in "はがもをのにへとで":
        return True                                     # 店は|どう, 東芝が|… but never 年に|は
    return _kind(a) == "hira" and _kind(b) in ("other", "kata", "num")


def wrap(text: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    """Wrap Japanese for big captions into lines of about equal width (no one-character last line), cutting
    at natural breaks (punctuation, or hiragana followed by a word) and never inside トイザらス or 市場."""
    total = f.getlength(text)
    n = max(1, math.ceil(total / width))
    target = total / n
    lines, start = [], 0
    for _ in range(n - 1):
        best, best_score = None, None
        for i in range(start + 1, len(text)):
            w = f.getlength(text[start:i])
            if w > width:
                break
            if text[i] in NO_LINE_START or text[i - 1] in NO_LINE_END:
                continue
            sc = abs(w - target) - (0.4 * target if _good_break(text, i) else 0)
            if best_score is None or sc < best_score:
                best, best_score = i, sc
        best = best or start + 1
        lines.append(text[start:best])
        start = best
    rest = text[start:]
    if rest:
        lines += wrap(rest, f, width) if f.getlength(rest) > width else [rest]
    return lines


def base_frame(img: Path, title: list[str]) -> Image.Image:
    src = Image.open(img).convert("RGB")
    s = max(W / src.width, H / src.height)
    bg = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    x, y = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(36))
    bg = Image.eval(bg, lambda v: int(v * 0.42))
    d = ImageDraw.Draw(bg)
    y = 150
    for i, t in enumerate(title):
        size = 118 if i == len(title) - 1 else 92
        f = font(TITLE_FONT, size)
        while f.getlength(t) > W - 80 and size > 50:
            size -= 4
            f = font(TITLE_FONT, size)
        d.text((W / 2, y), t, font=f, fill=GOLD if i == len(title) - 1 else "white", anchor="mt",
               stroke_width=10, stroke_fill="black")
        y += size + 24
    brand = font(TEXT_FONT, 34, black=True)
    d.text((W / 2, y + 6), CHANNEL["name"], font=brand, fill=(235, 200, 120), anchor="mt",
           stroke_width=4, stroke_fill="black")
    return bg


def caption_layer(text: str) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    size = CAP_SIZE
    while True:                       # at most 3 lines: shrink the type for a long sentence
        f = font(TEXT_FONT, size, black=True)
        rows = wrap(text, f, CAP_W)
        if len(rows) <= 3 or size <= 48:
            break
        size -= 6
    y = CAP_Y
    for ln in rows[:3]:
        d.text((W / 2, y), ln, font=f, fill="white", anchor="mt", stroke_width=9, stroke_fill="black")
        y += int(size * 1.3)
    return layer


def voice_line(ep: dict, text: str, mp3: Path, check: bool) -> float | None:
    cfg = CHANNEL["narrator"]
    speech = speech_for(text, ep.get("readings", {}), cfg.get("text_mode", "kanji"))
    key = json.dumps({"text": speech, "voice": cfg["voice_id"], "model": cfg["model_id"],
                      "settings": cfg["voice_settings"]}, ensure_ascii=False, sort_keys=True)
    meta = mp3.with_suffix(".json")
    if mp3.exists() and meta.exists() and json.loads(meta.read_text()).get("key") == key:
        return json.loads(meta.read_text()).get("cer")
    best = None
    for attempt in range(2):
        mp3.write_bytes(tts(speech, cfg))
        c = score([text], ep, heard(mp3))[0] if check else None
        best = c
        if c is None or c <= 0.08:
            break
        print(f"  {mp3.name}: reading error {c:.3f}, trying again", flush=True)
    meta.write_text(json.dumps({"key": key, "cer": best}, ensure_ascii=False))
    return best


def make_short(ep: dict, d: Path, spec: dict, check: bool):
    sid = spec["id"]
    vdir = d / "assets" / "shorts" / sid
    vdir.mkdir(parents=True, exist_ok=True)
    out = d / "out" / "shorts"
    out.mkdir(parents=True, exist_ok=True)

    # 1. voice, one file per line, and the timeline
    events, t, n = [], LEAD, 0
    report = []
    for si, scene in enumerate(spec["scenes"]):
        if si:
            t += SCENE_GAP - GAP
        for line in scene["lines"]:
            mp3 = vdir / f"line-{n:02d}.mp3"
            c = voice_line(ep, line, mp3, check)
            dur = duration(mp3)
            events.append({"scene": si, "text": display_text(line), "mp3": mp3, "start": t, "end": t + dur})
            report.append(f"{sid} line {n:02d}: {dur:.1f}s" + (f", reading error {c:.3f}" if c is not None else ""))
            t += dur + GAP
            n += 1
    total = events[-1]["end"] + TAIL
    print("\n".join(report))
    if total > 59.5:
        print(f"warning: {sid} is {total:.1f}s; Shorts must be under 60 s — cut a line", file=sys.stderr)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # 2. one clip per scene: blurred background + title, zooming picture, captions
        clips = []
        starts = [0.0] + [next(e["start"] for e in events if e["scene"] == si) for si in range(1, len(spec["scenes"]))]
        for si, scene in enumerate(spec["scenes"]):
            s0 = starts[si]
            s1 = starts[si + 1] if si + 1 < len(starts) else total
            dur = s1 - s0
            frames = max(1, round(dur * FPS))
            img = d / "assets" / "images" / f"{scene['image']}.png"
            base = tmp / f"base-{si}.png"
            base_frame(img, spec["title"]).save(base)
            ins = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(base), "-i", str(img)]
            graph = [f"[1:v]scale=3240:2160,zoompan=z='1+0.07*on/{frames}':x='iw/2-(iw/zoom/2)':"
                     f"y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{PHOTO_H}:fps={FPS}[ph]",
                     f"[0:v][ph]overlay=0:{PHOTO_Y}[v0]"]
            last = "v0"
            mine = [e for e in events if e["scene"] == si]
            for k, e in enumerate(mine):
                cap = tmp / f"cap-{si}-{k}.png"
                caption_layer(e["text"]).save(cap)
                ins += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(cap)]
                a = max(0.0, e["start"] - s0) if k else 0.0
                b = (mine[k + 1]["start"] - s0) if k + 1 < len(mine) else dur + 1
                graph.append(f"[{last}][{k + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{k + 1}]")
                last = f"v{k + 1}"
            clip = tmp / f"scene-{si}.mp4"
            sh(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(graph), "-map", f"[{last}]",
                "-frames:v", str(frames), "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                "-pix_fmt", "yuv420p", str(clip)])
            clips.append(clip)
        listing = tmp / "clips.txt"
        listing.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
        video = tmp / "video.mp4"
        sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(video)])

        # 3. narration placed on the timeline, BGM underneath, loudness for Shorts (-14 LUFS)
        ins, parts = [], []
        for i, e in enumerate(events):
            ins += ["-i", str(e["mp3"])]
            ms = int(e["start"] * 1000)
            parts.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[n{i}]")
        bgm = sorted((ROOT / "channel" / "bgm").glob("*.mp3"))[0]
        ins += ["-stream_loop", "-1", "-i", str(bgm)]
        k = len(events)
        graph = ";".join(parts) + ";" + "".join(f"[n{i}]" for i in range(k)) + \
            f"amix=inputs={k}:normalize=0:duration=longest,apad,atrim=0:{total:.3f},loudnorm=I=-14:TP=-2[voice];" \
            f"[{k}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo," \
            f"loudnorm=I=-33:TP=-9,afade=t=out:st={max(0.0, total - 1.5):.3f}:d=1.5[bgm];" \
            "[voice][bgm]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5,alimiter=limit=0.84[a]"
        audio = tmp / "audio.m4a"
        sh(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", graph, "-map", "[a]", "-c:a", "aac",
            "-b:a", "192k", str(audio)])
        # one-pass loudnorm overshoots on a clip this short: measure, then set the level with a plain gain
        r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(audio), "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True)
        measured = float(r.stderr.rsplit("I:", 1)[1].split("LUFS")[0])
        final = out / f"{sid}.mp4"
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(audio), "-map", "0:v", "-map", "1:a",
            "-af", f"volume={-14 - measured:.2f}dB,alimiter=limit=0.8:level=false", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final)])

    # 4. title, description and hashtags for the upload
    main_min = None
    main_mp4 = d / "out" / f"{d.name}.mp4"
    if main_mp4.exists():
        main_min = round(duration(main_mp4) / 60)
    tags = [CHANNEL["youtube"]["hashtag"]] + [h for h in spec.get("hashtags", []) if h != CHANNEL["youtube"]["hashtag"]]
    text = ["【タイトル】", spec["youtube_title"], "", "【説明】", *spec.get("description", []), "",
            f"本編{f'（約{main_min}分）' if main_min else ''}は、チャンネルの動画一覧からご覧いただけます。",
            CHANNEL["youtube"]["url"], "", " ".join("#" + h for h in tags + ["shorts"])]
    (out / f"{sid}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"{final} ({total:.1f}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--only")
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args()
    ep = load_episode(a.slug)
    d = episode_dir(a.slug)
    specs = ep.get("shorts", [])
    if a.only:
        specs = [s for s in specs if s["id"] in a.only.split(",")]
    if not specs:
        sys.exit("no shorts in episode.json")
    if not a.no_check:
        ensure_whisperx()
    for spec in specs:
        make_short(ep, d, spec, not a.no_check)


if __name__ == "__main__":
    main()
