from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run


class RuntimeTests(unittest.TestCase):
    def test_config_created_in_user_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            config = run.load_config(Path(temp))
            self.assertEqual(config['version'], '0.2.0')
            self.assertTrue((Path(temp) / 'config/app.json').is_file())

    def test_data_is_outside_application_bundle(self):
        with patch.object(Path, 'home', return_value=Path('/Users/host')):
            self.assertEqual(run.application_home(), Path('/Users/host/Library/Application Support/MusicaMac'))
