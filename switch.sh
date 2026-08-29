#!/usr/bin/env sh
# Compatibility launcher for users of the original `switch` command.
set -eu

if command -v git-multiple >/dev/null 2>&1; then
  exec git-multiple "$@"
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 -m git_multiple "$@"
