#!/bin/bash
set -euo pipefail
trap 'echo "Setup/launch failed. Check network and README.md. Press Return to close."; read -r answer' ERR
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/scripts/environment.sh"
exec "$PYTHON" "$ROOT/run.py"
