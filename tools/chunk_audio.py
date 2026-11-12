#!/usr/bin/env python3
"""Split a long video/audio into <=max_len second chunks at quiet points.

Usage: chunk_audio.py SOURCE OUT_DIR [--max 240]
Writes OUT_DIR/cNN.m4a and OUT_DIR/chunks.json ([{"file","start","end"}]).
Used to keep each WhisperX request short enough for the CLI request timeout.
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("source"); ap.add_argument("out"); ap.add_argument("--max", type=float, default=240)
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
sr = 16000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.source, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
dur = len(x) / sr
hop = int(sr * 0.05)
n = len(x) // hop
env = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
# smooth over 0.3 s so we pick inside a pause, not a stop consonant
k = 6
env = np.convolve(env, np.ones(k) / k, mode="same")
cuts = [0.0]
while dur - cuts[-1] > a.max:
    target = cuts[-1] + a.max
    lo, hi = int((target - 25) / 0.05), int(target / 0.05)
    lo = max(lo, int((cuts[-1] + 30) / 0.05))
    i = lo + int(np.argmin(env[lo:hi]))
    cuts.append(round(i * 0.05, 2))
cuts.append(round(dur, 3))
chunks = []
for j in range(len(cuts) - 1):
    f = out / f"c{j+1:02d}.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(cuts[j]), "-to", str(cuts[j + 1]), "-i", a.source,
                    "-vn", "-ac", "1", "-ar", "48000", "-c:a", "aac", "-b:a", "96k", str(f)], check=True)
    chunks.append({"file": f.name, "start": cuts[j], "end": cuts[j + 1]})
(out / "chunks.json").write_text(json.dumps(chunks, indent=2))
print(f"{len(chunks)} chunks, {dur:.1f}s")
