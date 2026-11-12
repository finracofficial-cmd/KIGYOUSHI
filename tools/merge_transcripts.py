#!/usr/bin/env python3
"""Merge chunk transcripts into one timed text and print narration statistics.

Usage: merge_transcripts.py <chunks-dir> <out.md> [--offsets 0,79.2,...] [--fix 山陽=三洋,...]
Chunk dirs made by chunk_audio.py carry their offsets in chunks.json.
"""
import argparse, json, re, statistics
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("dir"); ap.add_argument("out"); ap.add_argument("--offsets", default=""); ap.add_argument("--fix", default="")
a = ap.parse_args()
d = Path(a.dir)
if (d / "chunks.json").exists():
    chunks = json.loads((d / "chunks.json").read_text())
    items = [(d / (Path(c["file"]).stem + ".transcript.json"), c["start"]) for c in chunks]
else:
    offs = [float(x) for x in a.offsets.split(",")]
    items = [(p, offs[i]) for i, p in enumerate(sorted(d.glob("c*.transcript.json")))]
fixes = [f.split("=") for f in a.fix.split(",") if "=" in f]
words = []
for p, off in items:
    if not p.exists():
        continue
    for ps in json.loads(p.read_text())["passages"]:
        for w in ps["words"]:
            words.append((w["start_seconds"] + off, w["end_seconds"] + off, w["text"]))
words.sort()
# sentences: split at 。？！ ; record start/end
sents, cur = [], []
for w in words:
    cur.append(w)
    if re.search(r"[。？！?!]$", w[2]):
        sents.append(cur); cur = []
if cur:
    sents.append(cur)
def txt(s):
    t = "".join(w[2] for w in s).replace(" ", "")
    for a_, b_ in fixes:
        t = t.replace(a_, b_)
    return t
lines = []
for s in sents:
    t0 = s[0][0]
    lines.append(f"[{int(t0//60):02d}:{t0%60:04.1f}] {txt(s)}")
Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
total_chars = sum(len(re.sub(r"[、。？！「」・,.\s]", "", txt(s))) for s in sents)
speech = words[-1][1] - words[0][0]
lens = [len(txt(s)) for s in sents]
gaps = [sents[i+1][0][0] - sents[i][-1][1] for i in range(len(sents)-1)]
gaps = [g for g in gaps if 0 <= g < 5]
print(f"sentences {len(sents)}, chars(no punct) {total_chars}, span {speech/60:.1f} min, {total_chars/(speech/60):.0f} chars/min")
print(f"sentence length median {statistics.median(lens)}, p25 {statistics.quantiles(lens,n=4)[0]:.0f}, p75 {statistics.quantiles(lens,n=4)[2]:.0f}")
print(f"pause between sentences median {statistics.median(gaps):.2f}s, p75 {statistics.quantiles(gaps,n=4)[2]:.2f}s")
