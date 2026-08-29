#!/usr/bin/env sh
# Install Git Multiple from a source checkout without administrator privileges.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v git >/dev/null 2>&1; then
  echo "Error: Git is required but was not found on PATH." >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Error: Python 3.9 or newer is required for a source install." >&2
  echo "Alternatively, download the standalone binary from GitHub Releases." >&2
  exit 1
fi

"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' || {
  echo "Error: Python 3.9 or newer is required." >&2
  exit 1
}

"$PYTHON" -m pip install --user "$SCRIPT_DIR"

echo "Git Multiple was installed. Run: git-multiple doctor"
echo "If the command is not found, add your Python user scripts directory to PATH."
