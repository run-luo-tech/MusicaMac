import os
os.environ["SDL_AUDIODRIVER"] = "dummy"
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
import time
from types import SimpleNamespace
from unittest.mock import patch
from src.adapters.store import Store
from src.adapters.library import Library
from src.apps.desktop import Desktop, ImportDialog, APP_VERSION
from test_game import CONFIG

FIXTURE = Path(__file__).parent / "fixtures" / "silence.mp3"


class UITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)
        library = Library(self.store)
        library.import_mp3(FIXTURE, "SECRET ARTIST", "SECRET TITLE")
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = Desktop(self.root, self.store, CONFIG)

    def tearDown(self):
        self.app.audio.close()
        self.store.close()
        self.root.destroy()
        self.tmp.cleanup()

    def visible_text(self):
        result = []
        def scan(widget):
            if "text" in widget.keys():
                result.append(str(widget.cget("text")))
            for child in widget.winfo_children():
                scan(child)
        scan(self.root)
        return "\n".join(result)

    def test_reveal_clear_formal_lock_and_play_failure(self):
        self.app.next()
        self.assertNotIn("SECRET", self.visible_text())
        self.app.reveal()
        self.assertIn("SECRET TITLE", self.visible_text())
        self.app.start()
        self.assertNotIn("SECRET", self.visible_text())
        self.assertEqual(str(self.app.manage_button.cget("state")), "disabled")
        self.app.next()
        with patch.object(self.app.audio, "play", side_effect=RuntimeError("SECRET PATH")):
            self.app.begin_playback()
        self.assertFalse(self.store.used(self.app.game.session_id))
        self.assertNotIn("SECRET", self.visible_text())
        self.app.begin_playback()
        self.assertEqual(len(self.store.used(self.app.game.session_id)), 1)
        self.app.reveal()
        self.app.next()  # Exhausted: hide answer even when no next candidate.
        self.assertNotIn("SECRET", self.visible_text())
        with patch("src.apps.desktop.messagebox.askyesno", return_value=True):
            self.app.finish()
        self.assertFalse(self.app.game.formal)
        self.assertEqual(str(self.app.manage_button.cget("state")), "normal")

    def test_test_play_does_not_persist(self):
        self.app.next()
        self.app.begin_playback()
        self.assertIsNone(self.store.active())
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM plays").fetchone()[0], 0)

    def test_seek_preview_and_formal_play_counts_once(self):
        self.app.start()
        self.app.next()
        self.app.commit_seek(1.2)
        self.assertFalse(self.app.audio.loaded)
        self.assertEqual(self.app.pending_position, 1.2)
        self.assertEqual(len(self.store.history(self.app.game.session_id)), 0)
        self.app.play()
        # Native Tk rendering can take hundreds of ms while audio keeps playing.
        # Exact elapsed timing is tested directly in test_audio without UI work.
        self.assertEqual(self.app.audio.offset_ms, 1200)
        self.assertGreaterEqual(self.app.audio.position(), 1200)
        self.app.commit_seek(0.4)
        self.app.play()
        self.app.commit_seek(1.4)
        self.assertTrue(self.app.audio.paused)
        self.assertEqual(self.app.audio.position(), 1400)
        self.assertEqual(len(self.store.history(self.app.game.session_id)), 1)
        self.assertNotIn("SECRET", self.visible_text())
        self.app.replay()
        self.assertFalse(self.app.audio.paused)
        self.assertEqual(self.app.audio.offset_ms, 0)
        self.assertTrue(self.app.audio.busy())
        self.assertEqual(len(self.store.history(self.app.game.session_id)), 1)

    def test_mouse_drag_preview_is_not_overwritten_and_release_commits(self):
        self.root.deiconify()
        self.app.next()
        self.root.update()
        duration = self.app.game.current.duration
        left = self.app.progress.coords(0)[0]
        right = self.app.progress.coords(duration)[0]
        x = round(left + 0.6 * (right - left))
        self.app.progress.event_generate("<ButtonPress-1>", x=x, y=8)
        self.assertTrue(self.app.dragging)
        preview = self.app.progress_value.get()
        self.app.refresh_player()
        self.assertEqual(self.app.progress_value.get(), preview)
        self.app.progress.event_generate("<B1-Motion>", x=x + 10, y=8)
        self.app.progress.event_generate("<ButtonRelease-1>", x=x + 10, y=8)
        self.assertFalse(self.app.dragging)
        self.assertGreater(self.app.pending_position, duration * 0.6)
        self.assertFalse(self.app.audio.loaded)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM plays").fetchone()[0], 0)

    def test_switch_reset_keyboard_bounds_and_seek_failure(self):
        self.assertTrue(self.app.progress.instate(["disabled"]))
        self.app.next()
        self.app.seek_key(end=True)
        self.assertLess(self.app.pending_position, self.app.game.current.duration)
        self.app.seek_key(home=True)
        self.assertEqual(self.app.pending_position, 0)
        self.app.commit_seek(1.1)
        self.app.next()
        self.assertEqual(self.app.pending_position, 0)
        self.app.begin_playback()
        with patch.object(self.app.audio, "seek", side_effect=RuntimeError("SECRET PATH")):
            self.app.commit_seek(1)
        self.assertFalse(self.app.audio.loaded)
        self.assertIn("调整进度失败", self.visible_text())
        self.assertNotIn("SECRET", self.visible_text())

    def test_batch_preview_edit_and_error_remain_visible(self):
        bad = Path(self.tmp.name) / "Artist - Broken.mp3"
        bad.write_text("invalid mp3")
        parent = SimpleNamespace(window=self.root, app=self.app)
        dialog = ImportDialog(parent, [FIXTURE, bad])
        self.root.update()
        self.assertEqual(dialog.selected, 0)
        dialog.fields["artist"].set("Fixed artist")
        dialog.fields["title"].set("Fixed title")
        dialog.begin()
        for _ in range(100):
            self.root.update()
            if not dialog.running:
                break
            time.sleep(0.01)
        self.assertFalse(dialog.running)
        self.assertTrue(dialog.rows[0]["done"])
        self.assertIn("重复文件", dialog.rows[0]["status"])
        self.assertFalse(dialog.rows[1]["done"])
        self.assertIn("不是可读取", dialog.rows[1]["status"])
        dialog.table.selection_set("1")
        self.root.update()
        self.assertIn("不是可读取", dialog.rows[1]["status"])
        dialog.close()

    def test_preview_reads_artist_and_title_from_unspaced_filename(self):
        parent = SimpleNamespace(window=self.root, app=self.app)
        dialog = ImportDialog(parent, ["Beyond-情人.mp3", "陈奕迅-富士山下.mp3", "李健－贝加尔湖畔.mp3"])
        self.root.update()
        self.assertEqual(dialog.rows[0]["artist"], "Beyond")
        self.assertEqual(dialog.rows[0]["title"], "情人")
        self.assertEqual(dialog.rows[1]["artist"], "陈奕迅")
        self.assertEqual(dialog.rows[1]["title"], "富士山下")
        self.assertEqual(dialog.rows[2]["artist"], "李健")
        self.assertEqual(dialog.rows[2]["title"], "贝加尔湖畔")
        self.assertIn("v" + APP_VERSION, dialog.window.title())
        self.assertTrue(all(row["status"] == "待导入" for row in dialog.rows))
        self.assertEqual(dialog.fields["artist"].get(), "Beyond")
        self.assertEqual(dialog.fields["title"].get(), "情人")
        dialog.close()


if __name__ == "__main__":
    unittest.main()
