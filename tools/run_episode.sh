#!/usr/bin/env bash
# Produce an episode from episodes/<slug>/episode.json, end to end.
#
#   tools/run_episode.sh <slug> [stage...]
#
# Stages (default: all, in this order):
#   lint      check episode.json (readings for digits/Latin, images defined, caption length)
#   images    generate illustrations with OpenAI           (paid)
#   voice     generate narration with ElevenLabs           (paid)
#   assets    loudness, title/credits backgrounds, BGM bed
#   svml      write episode.svml / episode.svrun
#   render    hypit check + build (+ WhisperX alignment) and export out/<slug>.mp4
#   thumb     compose out/thumbnail.png
#   meta      write out/youtube.txt (title, description with chapter timestamps, tags)
#   review    write contact sheets of the finished video to out/review/
# Paid stages skip anything already generated with the same prompt/text.
set -euo pipefail
cd "$(dirname "$0")/.."
slug="${1:?usage: tools/run_episode.sh <slug> [stage...]}"
shift || true
stages=("$@")
[ ${#stages[@]} -eq 0 ] && stages=(lint images voice assets svml render thumb meta review)
ep="episodes/$slug"
[ -f "$ep/episode.json" ] || { echo "missing $ep/episode.json" >&2; exit 1; }
mkdir -p "$ep/out"

for stage in "${stages[@]}"; do
  echo "== $stage"
  case "$stage" in
    lint)
      (cd tools && python3 -c "
import sys
from episode_lib import load_episode, lint_episode
p = lint_episode(load_episode('$slug'))
print('\n'.join(p) or 'ok')
sys.exit(1 if p else 0)") ;;
    images) (cd tools && python3 gen_images.py "$slug") ;;
    voice)  (cd tools && python3 gen_voice.py "$slug") ;;
    assets) (cd tools && python3 prepare_assets.py "$slug") ;;
    svml)   (cd tools && python3 build_svml.py "$slug") ;;
    render)
      hypit check "$ep/episode.svrun"
      log="$ep/out/build.log"
      hypit build "$ep/episode.svrun" --title "$slug" --follow 2>&1 | tee "$log"
      id=$(grep -oE 'bld_[0-9A-Za-z_]+' "$log" | head -1)
      grep -q "Build failed" "$log" && { echo "build failed: see $log and 'hypit inspect $id'" >&2; exit 1; }
      rm -f "$ep/out/$slug.mp4"
      hypit get "$id" --output final.video --to "$ep/out/$slug.mp4"
      echo "$id" > "$ep/out/last-build-id" ;;
    thumb)  (cd tools && python3 make_thumbnail.py "$slug") ;;
    meta)   (cd tools && python3 youtube_meta.py "$slug") ;;
    review) python3 tools/review_sheets.py "$ep/out/$slug.mp4" "$ep/out/review" ;;
    *) echo "unknown stage $stage" >&2; exit 1 ;;
  esac
done
