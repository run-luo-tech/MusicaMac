from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run
from src.apps.desktop import APP_VERSION


class RuntimeTests(unittest.TestCase):
    def test_config_created_in_user_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            config = run.load_config(Path(temp))
            self.assertEqual(config['version'], APP_VERSION)
            self.assertTrue((Path(temp) / 'config/app.json').is_file())

    def test_data_is_outside_application_bundle(self):
        with patch.object(Path, 'home', return_value=Path('/Users/host')):
            self.assertEqual(run.application_home(), Path('/Users/host/Library/Application Support/MusicaMac'))

    def test_upgrade_preserves_existing_config_and_uses_new_version(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            config_path = directory / 'config/app.json'
            config_path.parent.mkdir()
            original = '{"schema_version":1,"volume":0.23,"selection":"random","version":"0.2.0"}'
            config_path.write_text(original, encoding='utf-8')
            config = run.load_config(directory)
            self.assertEqual(config['version'], APP_VERSION)
            self.assertEqual(config['volume'], 0.23)
            self.assertEqual(config_path.read_text(encoding='utf-8'), original)
