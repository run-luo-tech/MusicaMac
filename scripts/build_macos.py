"""Build and verify native DMG/ZIP distributions on the target Mac architecture."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile


def checked(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    if sys.platform != 'darwin':
        raise SystemExit('Build requires macOS; Windows cannot build a native Mac app.')
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))
    from src.apps.desktop import APP_VERSION
    from src.adapters.library import Library
    from src.adapters.store import Store
    architecture = platform.machine()
    if architecture not in {'arm64', 'x86_64'}:
        raise SystemExit('Unsupported Mac architecture: ' + architecture)
    if os.environ.get('MUSICA_EXPECTED_ARCH', architecture) != architecture:
        raise SystemExit('Runner architecture differs from the distribution label.')
    checked(sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v')
    checked(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--windowed', '--onedir',
                    '--name', 'Musica', '--osx-bundle-identifier', 'org.musica.mac',
            '--icon', str(root / 'assets/Musica.icns'), '--add-data', str(root / 'assets') + ':assets',
            '--target-architecture', architecture, '--specpath', 'build', 'run.py')
    package = root / 'dist' / 'Musica.app'
    plist_path = package / 'Contents/Info.plist'
    with plist_path.open('rb') as stream:
        info = plistlib.load(stream)
    info.update(CFBundleShortVersionString=APP_VERSION, CFBundleVersion=APP_VERSION)
    with plist_path.open('wb') as stream:
        plistlib.dump(info, stream)
    checked('/usr/bin/codesign', '--force', '--sign', '-', str(package))
    checked('/usr/bin/codesign', '--verify', '--deep', '--strict', str(package))
    binary_arch = checked('/usr/bin/lipo', '-archs', str(package / 'Contents/MacOS/Musica'),
                          capture_output=True, text=True).stdout.strip()
    if binary_arch != architecture:
        raise SystemExit('Packaged binary architecture mismatch: ' + binary_arch)
    source_commit = checked('git', 'rev-parse', 'HEAD', capture_output=True, text=True).stdout.strip()
    evidence = {'version': APP_VERSION, 'architecture': architecture, 'source_commit': source_commit,
                'macos': platform.mac_ver()[0], 'bundle_identifier': info['CFBundleIdentifier']}
    with tempfile.TemporaryDirectory(prefix='musica-upgrade-') as temporary_home:
        test_home = Path(temporary_home)
        old_home = test_home / 'Library/Application Support/MusicaMac'
        old_config = {'schema_version': 1, 'volume': 0.23, 'selection': 'random', 'version': '0.2.0'}
        config_path = old_home / 'config/app.json'
        config_path.parent.mkdir(parents=True)
        config_path.write_text(json.dumps(old_config), encoding='utf-8')
        store = Store(old_home / 'data')
        try:
            Library(store).import_mp3(root / 'tests/fixtures/silence.mp3', 'Synthetic artist', 'Upgrade fixture')
            session_id = store.start(old_config)
            store.record_play(session_id, store.songs()[0])
            database_before = '\n'.join(store.db.iterdump())
        finally:
            store.close()
        config_before = config_path.read_bytes()
        audio_path = old_home / 'data/audio/000001.mp3'
        audio_before = hashlib.sha256(audio_path.read_bytes()).hexdigest()
        report = test_home / 'packaged-smoke.json'
        environment = dict(os.environ, HOME=temporary_home, SDL_AUDIODRIVER='dummy')
        checked(str(package / 'Contents/MacOS/Musica'), '--smoke-report', str(report),
                env=environment, timeout=45)
        smoke = json.loads(report.read_text(encoding='utf-8'))
        if not smoke['success']:
            raise SystemExit('Packaged smoke failed: ' + repr(smoke))
        with closing(sqlite3.connect(old_home / 'data/library.db')) as database:
            assert '\n'.join(database.iterdump()) == database_before
        assert config_path.read_bytes() == config_before
        assert hashlib.sha256(audio_path.read_bytes()).hexdigest() == audio_before
        evidence['packaged_smoke'] = smoke
        evidence['upgrade_data_preserved'] = True
    name = f'MusicaMac-{architecture}-v{APP_VERSION}'
    output = root / 'releases' / name
    output.mkdir(parents=True, exist_ok=True)
    # Stage only explicitly public files, excluding developer data and environments.
    with tempfile.TemporaryDirectory(prefix='musica-distribution-') as temporary:
        payload = Path(temporary) / name
        payload.mkdir()
        checked('/usr/bin/ditto', str(package), str(payload / 'Musica.app'))
        (payload / 'Applications').symlink_to('/Applications', target_is_directory=True)
        for document in ('README.md', 'THIRD_PARTY_NOTICES.md'):
            shutil.copy2(root / document, payload / document)
        shutil.copytree(root / 'licenses', payload / 'licenses')
        shutil.copy2(root / 'docs/manual/Musica-使用说明书.pdf', payload)
        archive = output / f'{name}.zip'
        checked('/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(payload), str(archive))
        dmg = output / f'{name}.dmg'
        checked('/usr/bin/hdiutil', 'create', '-volname', f'Musica {APP_VERSION}', '-srcfolder', str(payload),
                '-format', 'UDZO', '-fs', 'HFS+', '-ov', str(dmg))
        checked('/usr/bin/hdiutil', 'verify', str(dmg))
    evidence['files'] = {path.name: {'size': path.stat().st_size,
                                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                         for path in (archive, dmg)}
    (output / 'build-verification.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    print('Ad-hoc signed native distribution; Developer ID notarization is not configured.')


if __name__ == '__main__':
    main()
