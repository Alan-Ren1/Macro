#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! python3 - <<'PY' >/dev/null 2>&1
import sys
try:
    import pyautogui
except Exception:
    sys.exit(1)
PY
then
  python3 -m pip install -r requirements.txt >/dev/null 2>&1 || true
fi

python3 anime_expedition_macro.py "$@"
