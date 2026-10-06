#!/usr/bin/env bash
# Render the deck to docs/. Parallel builders share one working tree, so
# renders are serialised with a lock directory (macOS has no flock).
set -euo pipefail
cd "$(dirname "$0")/.."
lock=.render.lock
for _ in $(seq 1 600); do
  if mkdir "$lock" 2>/dev/null; then break; fi
  sleep 1
done
trap 'rmdir "$lock"' EXIT
uv run quarto render index.qmd "$@"
