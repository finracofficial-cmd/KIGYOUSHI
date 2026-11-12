#!/usr/bin/env python3
"""Generate the episode's illustrations with the OpenAI Images API.

Each entry in episode.json "images" has a "prompt" describing the scene; the channel's shared
style (channel/channel.json image.style) is appended so every episode keeps one look. Writes
episodes/<slug>/assets/images/<image-id>.png and skips images that already exist with the same
prompt (a .prompt.txt copy sits beside each image). Needs OPENAI_API_KEY. Billed per image.

Usage: gen_images.py <slug> [--only id1,id2] [--force] [--dry-run] [--jobs 3]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from episode_lib import CHANNEL, episode_dir, load_episode


def full_prompt(scene: str) -> str:
    return f"{scene.strip()}\n\nStyle: {CHANNEL['image']['style']}"


def generate(prompt: str) -> bytes:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not set")
    cfg = CHANNEL["image"]
    body = {"model": cfg["model"], "prompt": prompt, "size": cfg["size"], "quality": cfg["quality"], "n": 1}
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=json.dumps(body).encode(),
                                 method="POST", headers={"Authorization": f"Bearer {key}",
                                                         "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = json.loads(r.read())
            return base64.b64decode(data["data"][0]["b64_json"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"OpenAI HTTP {e.code}: {msg}")
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            if attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"network error: {e}")
    raise RuntimeError("unreachable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    ep = load_episode(a.slug)
    out = episode_dir(a.slug) / "assets" / "images"
    out.mkdir(parents=True, exist_ok=True)
    only = set(filter(None, a.only.split(",")))
    todo = []
    for iid, spec in ep["images"].items():
        if only and iid not in only:
            continue
        png, ptxt = out / f"{iid}.png", out / f"{iid}.prompt.txt"
        prompt = full_prompt(spec["prompt"])
        if not a.force and png.exists() and ptxt.exists() and ptxt.read_text(encoding="utf-8") == prompt:
            continue
        todo.append((iid, png, ptxt, prompt))
    print(f"{len(todo)} image(s) to generate")
    if a.dry_run:
        for iid, *_ in todo:
            print(" ", iid)
        return

    def run(item):
        iid, png, ptxt, prompt = item
        try:
            png.write_bytes(generate(prompt))
            ptxt.write_text(prompt, encoding="utf-8")
            return f"{iid}: ok"
        except Exception as e:  # report and continue with the others
            return f"{iid}: FAILED {e}"

    failed = 0
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for msg in ex.map(run, todo):
            print(msg)
            failed += "FAILED" in msg
    if failed:
        sys.exit(f"{failed} image(s) failed")


if __name__ == "__main__":
    main()
