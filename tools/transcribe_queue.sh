#!/usr/bin/env bash
# Transcribe every chunk listed on the command line (dirs containing chunks.json), one at a time.
# Creates <dir>/<chunk>.transcript.json; skips finished ones. Pauses while .whisperx-pause exists
# so a Hypit build can use the single local WhisperX service.
set -u
for dir in "$@"; do
  for f in "$dir"/c*.m4a "$dir"/c*.mp4; do
    [ -e "$f" ] || continue
    out="${f%.*}.transcript.json"
    [ -s "$out" ] && continue
    while [ -e .whisperx-pause ]; do sleep 5; done
    if hypit transcribe "$f" --language ja --to "$out" >/dev/null 2>"${f%.*}.err"; then echo "ok $f"; else echo "FAILED $f: $(tail -2 "${f%.*}.err" | tr '\n' ' ')"; fi
  done
done
echo "queue done"
