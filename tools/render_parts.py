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
import shutil
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


def ensure_services(need_whisperx: bool = True):
    """WhisperX (large-v3) holds several GB even when idle. A part whose alignment is reused from an earlier build
    does not need it, and rendering next to it can run out of memory, so it is stopped for such parts."""
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=5).read()
        running = True
    except Exception:
        running = False
    if need_whisperx and not running:
        print("starting WhisperX", flush=True)
        sh(["hypit", "programs", "up", "--endpoint", "whisperx.local"], check=True, stdout=subprocess.DEVNULL)
    elif not need_whisperx and running:
        print("stopping WhisperX (alignment is reused)", flush=True)
        sh(["hypit", "programs", "down", "--endpoint", "whisperx.local"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sh(["hypit", "runtime", "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def status(bid: str) -> dict | None:
    """One build as the Worker sees it ({"work": ..., "result": ...}), or None when it cannot be read.
    (`hypit activity` is avoided: it loads every unfinished Result and can take gigabytes.)"""
    for _ in range(3):
        r = sh(["hypit", "status", bid, "--json"], capture_output=True, text=True)
        try:
            return json.loads(r.stdout)["build"]
        except (json.JSONDecodeError, KeyError):
            time.sleep(20)
    return None


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
    print(f"{part['name']}: picking up earlier build {bid}", flush=True)
    return bid if wait_build(bid) else None


def wait_build(bid: str) -> bool:
    """Wait until the Worker has finished a build, by polling `hypit status` (the Worker's own state).
    Restarts the runtime once if the build stops moving for 20 minutes. True when the Result is complete."""
    last, since, restarted = None, time.time(), False
    while True:
        b = status(bid)
        if b is None:
            sys.exit(f"cannot read the state of build {bid}; is the runtime up? (`hypit runtime up`)")
        if b["work"]["state"] != "working":
            break
        mark = json.dumps([b["work"].get("requests"), b.get("commands"), b["result"].get("outputCount")])
        if mark != last:
            last, since = mark, time.time()
        elif time.time() - since > 20 * 60 and not restarted:
            # the Worker process can die while the runtime still reports it as running (seen after a session
            # restart): nothing moves. Restarting the runtime lets the queued build continue.
            print(f"build {bid} has not moved for 20 minutes; restarting the Hypit runtime", flush=True)
            sh(["hypit", "runtime", "down"], capture_output=True)
            sh(["hypit", "runtime", "up"], capture_output=True)
            since, restarted = time.time(), True
        time.sleep(60)
    finish = ["hypit", "result", "finish", bid, "--project", str(ROOT), "--runtime", str(ROOT / "hypit.runtime.json")]
    if b.get("attention") or b["result"].get("state") == "open":
        # e.g. the result save ran out of memory; finishing it recovers the outputs
        sh(finish, capture_output=True)
        b = status(bid) or b
        if "already owned" in (b.get("attention") or {}).get("message", ""):
            # the process that was saving it died; a runtime restart releases its claim
            sh(["hypit", "runtime", "down"], capture_output=True)
            sh(["hypit", "runtime", "up"], capture_output=True)
            sh(finish, capture_output=True)
            b = status(bid) or b
    return b["result"].get("state") == "complete"


def render(d: Path, part: dict) -> str:
    svrun = d / part["svrun"]
    if sh(["hypit", "check", str(svrun)], capture_output=True, text=True).returncode != 0:
        r = sh(["hypit", "check", str(svrun)], capture_output=True, text=True)
        sys.exit(f"{part['name']}: check failed\n{r.stdout}{r.stderr}")
    log = d / "out" / "parts" / f"{part['name']}.build.log"
    (d / "out" / "parts" / f"{part['name']}.pending").write_text(part["fingerprint"])
    with open(log, "w") as f:
        # submit only; wait_build() polls the Worker (a --follow client can hang when the Worker dies)
        sh(["hypit", "build", str(svrun), "--title", f"{d.name}-{part['name']}"], stdout=f, stderr=subprocess.STDOUT)
    text = log.read_text(errors="replace")
    m = re.search(r"bld_[0-9A-Za-z_]+", text)
    if not m:
        sys.exit(f"{part['name']}: no build id; see {log}")
    bid = m.group()
    if not wait_build(bid) or "Build failed" in text or "Execution  failed" in text:
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
            free_gb = shutil.disk_usage(ROOT).free / 1e9
            if free_gb < 2:
                sys.exit(f"only {free_gb:.1f} GB of disk left; a part needs about 1 GB while it renders. Delete finished "
                         "episodes' old builds under .hypit/results/<date>/ (keep the ones out/align-cache.json names) and rerun")
            svrun_text = (d / part["svrun"]).read_text()
            ensure_services(need_whisperx=not all(f'output="{sid}-align.alignment"' in svrun_text for sid in part["segments"]))
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
