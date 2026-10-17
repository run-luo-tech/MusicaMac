import csv
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from mutagen.id3 import ID3, TIT2
from src.adapters.store import Store
from src.adapters.library import Library

FIXTURE = Path(__file__).parent / "fixtures" / "silence.mp3"


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / "data")
        self.library = Library(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def source(self, title="SECRET TITLE"):
        target = self.root / (str(len(list(self.root.glob("*.mp3")))) + ".mp3")
        target.write_bytes(FIXTURE.read_bytes())
        tags = ID3(target)
        tags.add(TIT2(encoding=3, text=title))
        tags.save(target)
        return target

    def test_import_duplicate_strip_metadata_and_preserve_source(self):
        source = self.source()
        before = hashlib.sha256(source.read_bytes()).digest()
        code, added = self.library.import_mp3(source, "歌手", "歌曲")
        self.assertTrue(added)
        self.assertEqual(code, 1)
        self.assertEqual(self.store.audio_path(code).name, "000001.mp3")
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), before)
        with self.assertRaises(Exception):
            ID3(self.store.audio_path(code))
        self.assertEqual(self.library.import_mp3(source, "歌手", "歌曲"), (1, False))
        self.assertGreater(self.store.song(code).duration, 1)

    def test_invalid_extension_content_missing_name_and_conflict(self):
        wrong = self.root / "not.mp3"
        wrong.write_text("not audio")
        with self.assertRaises(ValueError):
            self.library.import_mp3(wrong, "A", "B")
        with self.assertRaises(ValueError):
            self.library.import_mp3(self.root / "not.wav", "A", "B")
        with self.assertRaises(ValueError):
            self.library.import_mp3(FIXTURE, "", "B")
        self.library.import_mp3(self.source("v1"), "A", "B")
        different = self.source("v2")
        with self.assertRaises(ValueError):
            self.library.import_mp3(different, "A", "B")
        self.library.import_mp3(different, "A", "B", "现场版")
        self.assertEqual(len({s.group_key for s in self.store.songs()}), 1)

    def test_export_escapes_and_keeps_code(self):
        self.library.import_mp3(FIXTURE, "<script>alert(1)</script>", "A & B")
        html = self.root / "answers.html"
        self.library.export_html(html)
        text = html.read_text(encoding="utf-8")
        self.assertIn("&lt;script&gt;", text)
        self.assertNotIn("<script>alert", text)
        self.assertIn("000001", text)
        self.assertIn("A &amp; B", text)
        self.assertNotIn("src=\"http", text)
        csv_path = self.root / "answers.csv"
        self.library.export_csv(csv_path)
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[1][0], "000001")

    def test_import_rejected_for_unfinished_activity(self):
        self.store.start({})
        with self.assertRaises(ValueError):
            self.library.import_mp3(FIXTURE, "A", "B")

    def test_audio_stream_pause_resume_and_failure(self):
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        from src.adapters.audio import Audio
        audio = Audio(0)
        try:
            audio.play(FIXTURE)
            self.assertTrue(audio.busy())
            audio.toggle()
            self.assertTrue(audio.paused)
            audio.toggle()
            self.assertFalse(audio.paused)
            audio.stop()
            with self.assertRaises(RuntimeError):
                audio.play(self.root / "missing.mp3")
            self.assertFalse(audio.loaded)
        finally:
            audio.close()


if __name__ == "__main__":
    unittest.main()
