#!/usr/bin/env sh
set -e
cd "$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/build_tui.py "$@"
else
  exec python scripts/build_tui.py "$@"
fi
