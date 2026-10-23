#!/bin/bash
set -euo pipefail
trap 'echo "Build failed. See terminal output."; if [ -t 0 ]; then read -r answer; fi' ERR
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/scripts/environment.sh"
"$UV" pip install --python "$PYTHON" --only-binary :all: -r "$ROOT/requirements-build.txt"
exec "$PYTHON" "$ROOT/scripts/build_macos.py"
