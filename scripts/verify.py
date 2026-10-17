"""Run acceptance with the activated/private interpreter, including Windows venv launchers."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
environment = Path(os.environ.get('VIRTUAL_ENV', root / '.venv'))
candidate = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
python = str(candidate) if candidate.is_file() else sys.executable
raise SystemExit(subprocess.call([python, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=root))
