"""Real MP3 positioning plus failure handling without publishing private paths."""
import os
os.environ["SDL_AUDIODRIVER"] = "dummy"
from pathlib import Path
import time
import unittest
from unittest.mock import patch
from src.adapters.audio import Audio

FIXTURE = Path(__file__).parent / "fixtures" / "silence.mp3"


class SeekTests(unittest.TestCase):
    def setUp(self):
        self.audio = Audio(0)

    def tearDown(self):
        self.audio.close()

    def test_real_mp3_absolute_start_forward_backward_pause_resume(self):
        self.audio.play(FIXTURE, start=0.7)
        self.assertTrue(self.audio.busy())
        self.assertAlmostEqual(self.audio.position(), 700, delta=150)
        self.audio.seek(1.6)
        self.assertAlmostEqual(self.audio.position(), 1600, delta=150)
        self.audio.seek(0.3)
        self.assertAlmostEqual(self.audio.position(), 300, delta=150)
        self.audio.toggle()
        self.audio.seek(1.1)
        self.assertTrue(self.audio.paused)
        self.assertFalse(self.audio.busy())
        time.sleep(0.06)
        self.assertEqual(self.audio.position(), 1100)
        self.audio.toggle()
        time.sleep(0.06)
        self.assertTrue(self.audio.busy())
        self.assertGreaterEqual(self.audio.position(), 1100)
        self.assertLess(self.audio.position(), 1400)
        self.audio.stop()
        self.assertEqual(self.audio.position(), 0)

    def test_seek_after_end_remains_paused_until_requested(self):
        self.audio.play(FIXTURE)
        with patch.object(self.audio, "busy", return_value=False):
            self.audio.seek(0.5)
        self.assertTrue(self.audio.paused)
        self.assertEqual(self.audio.position(), 500)

    def test_failed_seek_stops_and_does_not_expose_underlying_error(self):
        self.audio.play(FIXTURE)
        with patch("src.adapters.audio.pygame.mixer.music.play", side_effect=RuntimeError("SECRET PATH")):
            with self.assertRaisesRegex(RuntimeError, "调整进度失败") as raised:
                self.audio.seek(1)
        self.assertNotIn("SECRET", str(raised.exception))
        self.assertFalse(self.audio.loaded)
        self.assertEqual(self.audio.position(), 0)

    def test_invalid_positions_do_not_interrupt_audio(self):
        self.audio.play(FIXTURE)
        for value in (-1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.audio.seek(value)
        self.assertTrue(self.audio.busy())
