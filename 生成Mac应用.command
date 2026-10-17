#!/bin/bash
set -euo pipefail
trap 'echo "Build failed. See terminal output. Press Return to close."; read -r answer' ERR
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/scripts/environment.sh"
"$UV" pip install --python "$PYTHON" --only-binary :all: -r "$ROOT/requirements-build.txt"
exec "$PYTHON" "$ROOT/scripts/build_macos.py"
