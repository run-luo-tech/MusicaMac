"""Verify downloaded Mac build artifacts against the actual workflow and bundle."""
import ast
import hashlib
import json
from pathlib import Path
import plistlib
import struct
import subprocess
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / 'src/apps/desktop.py').read_text(encoding='utf-8'))
    version = next(node.value.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'APP_VERSION' for target in node.targets))
    workflow = json.loads((root / '.engineering/native-workflow.json').read_text(encoding='utf-8-sig'))
    assert workflow['conclusion'] == 'success'
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert workflow['head_sha'] == commit, 'Workflow must build the current source commit'
    results = []
    for architecture, cpu in (('arm64', 0x0100000c), ('x86_64', 0x01000007)):
        candidates = list((root / f'releases/ci-v{version}').rglob('build-verification.json'))
        evidence = next((path, json.loads(path.read_text(encoding='utf-8'))) for path in candidates
                        if json.loads(path.read_text(encoding='utf-8'))['architecture'] == architecture)
        path, build = evidence
        assert build['version'] == version and build['source_commit'] == commit
        assert build['bundle_identifier'] == 'org.musica.mac'
        assert build['packaged_smoke']['success'] and build['upgrade_data_preserved']
        for filename, expected in build['files'].items():
            package = path.parent / filename
            assert package.stat().st_size == expected['size']
            assert hashlib.sha256(package.read_bytes()).hexdigest() == expected['sha256']
        archive_path = path.parent / f'MusicaMac-{architecture}-v{version}.zip'
        with zipfile.ZipFile(archive_path) as archive:
            prefix = f'MusicaMac-{architecture}-v{version}/'
            bundle = prefix + 'Musica.app/Contents/'
            info = plistlib.loads(archive.read(bundle + 'Info.plist'))
            assert info['CFBundleIdentifier'] == 'org.musica.mac'
            assert info['CFBundleShortVersionString'] == version and info['CFBundleVersion'] == version
            with archive.open(bundle + 'MacOS/Musica') as binary:
                magic, actual_cpu = struct.unpack('<II', binary.read(8))
            assert magic == 0xfeedfacf and actual_cpu == cpu, 'Mach-O architecture mismatch'
            assert prefix + 'Applications' in archive.namelist()
            assert not any(name.startswith(prefix + folder + '/') for folder in ('data', 'config', '.venv', '.runtime')
                           for name in archive.namelist())
        results.append({'architecture': architecture, 'macos': build['macos'], 'files': build['files']})
    result = {'version': version, 'source_commit': commit, 'workflow_url': workflow['html_url'], 'builds': results}
    (root / '.engineering/native-artifacts-verified.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
