"""Build a self-contained .app on a Mac of the target architecture."""
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    if sys.platform != 'darwin':
        raise SystemExit('Build requires macOS; Windows cannot build a native Mac app.')
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    architecture = platform.machine()
    if architecture not in {'arm64', 'x86_64'}:
        raise SystemExit('Unsupported Mac architecture: ' + architecture)
    import tkinter
    window = tkinter.Tk()
    window.withdraw()
    window.update()
    window.destroy()
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], check=True)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--windowed', '--onedir',
                    '--name', 'Musica', '--osx-bundle-identifier', 'org.musica.mac',
                    '--target-architecture', architecture, '--specpath', 'build', 'run.py'], check=True)
    package = root / 'dist' / 'Musica.app'
    with tempfile.TemporaryDirectory() as temporary_home:
        environment = dict(os.environ, HOME=temporary_home, SDL_AUDIODRIVER='dummy')
        process = subprocess.Popen([str(package / 'Contents/MacOS/Musica')], env=environment)
        time.sleep(4)
        if process.poll() is not None:
            raise SystemExit('Packaged app exited during startup; distribution stopped.')
        process.terminate()
        process.wait(timeout=10)
    output = root / 'releases' / f'MusicaMac-{architecture}-v0.2.0'
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'MusicaMac-{architecture}-v0.2.0.zip'
    subprocess.run(['/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(package), str(archive)], check=True)
    for document in ['README.md', 'THIRD_PARTY_NOTICES.md']:
        shutil.copy2(root / document, output / document)
    pdf = root / 'docs/manual/Musica-使用说明书.pdf'
    if pdf.exists():
        shutil.copy2(pdf, output / pdf.name)
    print('Built native app for', architecture, ':', archive)
    print('Ad-hoc signature only. Developer ID signing/notarization is a separate release step.')


if __name__ == '__main__':
    main()
