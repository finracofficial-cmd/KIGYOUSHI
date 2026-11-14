#!/usr/bin/env python3
"""Render an episode's parts with Hypit, join them, and lay the background music under the film.

Reads out/parts.json written by build_svml.py. A part whose fingerprint matches its last successful
render (out/parts/<name>.fingerprint) is not rendered again. A build cut off by a tool time limit keeps
running in the Hypit Worker; the next run waits for it (out/parts/<name>.pending) instead of starting over. After each successful part, the
alignment of its segments is recorded in out/align-cache.json so later builds can reuse it.

Writes out/parts/<name>.mp4 and the finished out/<slug>.mp4.
Usage: render_parts.py <slug> [--force]
"""
from __future__ import annotations

import json
import time
import os
import re
import subprocess
import sys
from pathlib import Path

from episode_lib import ROOT, episode_dir

ENV = {**os.environ, "NODE_OPTIONS": (os.environ.get("NODE_OPTIONS", "") + " --max-old-space-size=6144").strip()}


def sh(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, env=ENV, **kw)


def duration(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


def ensure_services():
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=5).read()
    except Exception:
        print("starting WhisperX", flush=True)
        sh(["hypit", "programs", "up", "--endpoint", "whisperx.local"], check=True, stdout=subprocess.DEVNULL)
    sh(["hypit", "runtime", "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def activity() -> dict:
    """Builds the Worker knows about, by id."""
    r = sh(["hypit", "activity", "--json"], capture_output=True, text=True)
    try:
        return {b["id"]: b for b in json.loads(r.stdout).get("builds", [])}
    except (json.JSONDecodeError, AttributeError):
        return {}


def adopt(d: Path, part: dict) -> str | None:
    """A build of this exact part started by an earlier run that was cut off (the build keeps going in the
    Worker). Wait for it and return its id, or None when there is nothing to adopt."""
    pend = d / "out" / "parts" / f"{part['name']}.pending"
    log = d / "out" / "parts" / f"{part['name']}.build.log"
    if not (pend.exists() and log.exists()) or pend.read_text() != part["fingerprint"]:
        return None
    m = re.search(r"bld_[0-9A-Za-z_]+", log.read_text(errors="replace"))
    if not m:
        return None
    bid = m.group()
    while True:
        b = activity().get(bid)
        if not b or b["work"]["state"] != "working":
            break
        print(f"{part['name']}: waiting for earlier build {bid} ({', '.join(b.get('phases', {})) or 'working'})", flush=True)
        time.sleep(60)
    if b and b["work"].get("outcome") == "failed" and "attention" not in b:
        return None
    if b and "attention" in b:
        sh(["hypit", "result", "finish", bid, "--project", str(ROOT), "--runtime", str(ROOT / "hypit.runtime.json")],
           capture_output=True)
    return bid


def render(d: Path, part: dict) -> str:
    svrun = d / part["svrun"]
    if sh(["hypit", "check", str(svrun)], capture_output=True, text=True).returncode != 0:
        r = sh(["hypit", "check", str(svrun)], capture_output=True, text=True)
        sys.exit(f"{part['name']}: check failed\n{r.stdout}{r.stderr}")
    log = d / "out" / "parts" / f"{part['name']}.build.log"
    (d / "out" / "parts" / f"{part['name']}.pending").write_text(part["fingerprint"])
    with open(log, "w") as f:
        sh(["hypit", "build", str(svrun), "--title", f"{d.name}-{part['name']}", "--follow"], stdout=f, stderr=subprocess.STDOUT)
    text = log.read_text(errors="replace")
    m = re.search(r"bld_[0-9A-Za-z_]+", text)
    if not m:
        sys.exit(f"{part['name']}: no build id; see {log}")
    bid = m.group()
    if "needs attention" in text:
        sh(["hypit", "result", "finish", bid, "--project", str(ROOT), "--runtime", str(ROOT / "hypit.runtime.json")],
           capture_output=True)
    if "Build failed" in text or "Execution  failed" in text:
        sys.exit(f"{part['name']}: build failed ({bid}); see {log} and `hypit inspect {bid}`")
    return bid


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    slug, force = sys.argv[1], "--force" in sys.argv
    d = episode_dir(slug)
    parts = json.loads((d / "out" / "parts.json").read_text())
    pdir = d / "out" / "parts"
    pdir.mkdir(parents=True, exist_ok=True)
    pending = json.loads((d / "out" / "align-pending.json").read_text())
    cache_p = d / "out" / "align-cache.json"

    for part in parts:
        mp4, fpf = pdir / f"{part['name']}.mp4", pdir / f"{part['name']}.fingerprint"
        if not force and mp4.exists() and fpf.exists() and fpf.read_text() == part["fingerprint"]:
            print(f"{part['name']}: unchanged, kept")
            continue
        ensure_services()
        r = None
        bid = None if force else adopt(d, part)
        if bid:
            mp4.unlink(missing_ok=True)
            r = sh(["hypit", "get", bid, "--output", "final.video", "--to", str(mp4)], capture_output=True, text=True)
            if r.returncode != 0:
                print(f"{part['name']}: earlier build {bid} has no video; rendering again", flush=True)
                bid = None
        if not bid:
            print(f"{part['name']}: rendering {', '.join(part['segments'])}", flush=True)
            bid = render(d, part)
            mp4.unlink(missing_ok=True)
            r = sh(["hypit", "get", bid, "--output", "final.video", "--to", str(mp4)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"{part['name']}: export failed\n{r.stdout}{r.stderr}")
        fpf.write_text(part["fingerprint"])
        (pdir / f"{part['name']}.pending").unlink(missing_ok=True)
        cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
        for sid in part["segments"]:
            if cache.get(sid, {}).get("hash") != pending[sid]:
                cache[sid] = {"hash": pending[sid], "build": bid}
        cache_p.write_text(json.dumps(cache, indent=1))
        print(f"{part['name']}: done ({bid}, {duration(mp4):.1f}s)", flush=True)

    # join the parts without re-encoding, then mix the music bed under the narration
    listing = pdir / "concat.txt"
    listing.write_text("".join(f"file '{(pdir / (p['name'] + '.mp4')).as_posix()}'\n" for p in parts))
    joined = pdir / "joined.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy",
                    str(joined)], check=True)
    total = duration(joined)
    bed = d / "assets" / "derived" / "bgm-bed.m4a"
    final = d / "out" / f"{slug}.mp4"
    graph = (f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=1.5,"
             f"afade=t=out:st={max(0.0, total - 3):.3f}:d=3[bgm];"
             "[0:a]aresample=48000,aformat=channel_layouts=stereo[voice];"
             "[voice][bgm]amix=inputs=2:normalize=0:duration=first[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-i", str(bed), "-filter_complex", graph,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", str(final)], check=True)
    print(f"{final} ({total / 60:.1f} min)")


if __name__ == "__main__":
    main()
