#!/bin/bash
set -euo pipefail
if [ "$(uname -s)" != Darwin ]; then
  echo 'This setup command is for macOS only.' >&2
  exit 1
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export UV_PYTHON_INSTALL_DIR="$ROOT/.runtime/python"
export UV_CACHE_DIR="$ROOT/.runtime/cache"
UV="$ROOT/.runtime/bin/uv"
mkdir -p "$ROOT/.runtime/bin"
if [ ! -x "$UV" ]; then
  echo 'First setup: download uv from astral.sh. No sudo or shell profile changes.'
  installer="$ROOT/.runtime/uv-install.sh"
  curl --fail --location --show-error --proto '=https' --tlsv1.2 https://astral.sh/uv/install.sh -o "$installer"
  env UV_UNMANAGED_INSTALL="$ROOT/.runtime/bin" sh "$installer"
fi
cd "$ROOT"
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  "$UV" python install --managed-python 3.12
  "$UV" venv --managed-python --python 3.12 "$ROOT/.venv"
fi
checksum="$(shasum -a 256 "$ROOT/requirements.txt" | cut -d ' ' -f 1)"
if [ ! -f "$ROOT/.runtime/requirements.sha256" ] || [ "$(cat "$ROOT/.runtime/requirements.sha256")" != "$checksum" ]; then
  "$UV" pip install --python "$ROOT/.venv/bin/python" --only-binary :all: -r "$ROOT/requirements.txt"
  "$ROOT/.venv/bin/python" -c 'import tkinter,pygame,mutagen; print("Runtime ready; Tk",tkinter.TkVersion)'
  printf '%s' "$checksum" > "$ROOT/.runtime/requirements.sha256"
fi
PYTHON="$ROOT/.venv/bin/python"
