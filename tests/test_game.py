import json
from pathlib import Path
import tempfile
import unittest
from src.core.models import group_key, parse_filename, choose_song
from src.adapters.store import Store, now
from src.pipelines.game import Game

CONFIG = {"schema_version": 1, "volume": 0.65, "selection": "random", "version": "0.1.0"}


def insert_song(store, artist, title, version="", digest=None):
    with store.db:
        result = store.db.execute(
            "INSERT INTO songs(artist,title,version,group_key,duration,sha256,created_at) VALUES (?,?,?,?,?,?,?)",
            (artist, title, version, group_key(artist, title), 3.0, digest or artist + title + version, now()))
    return store.song(result.lastrowid)


class GameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)
        self.a = insert_song(self.store, "A", "Alpha")
        self.b = insert_song(self.store, "B", "Beta")
        self.a_live = insert_song(self.store, "A", "Alpha", "Live")
        self.game = Game(self.store, CONFIG)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_name_and_group(self):
        self.assertEqual(parse_filename("歌手 - 歌名 - 副标题"), ("歌手", "歌名 - 副标题"))
        self.assertEqual(parse_filename("未规范命名"), ("", "未规范命名"))
        self.assertEqual(group_key(" A  B ", "ABC"), group_key("a b", "abc"))

    def test_filename_without_spaces_from_import_preview(self):
        examples = [
            ("AGA江海迦-孤雏", "AGA江海迦", "孤雏"),
            ("Beyond-情人", "Beyond", "情人"),
            ("陈奕迅-富士山下", "陈奕迅", "富士山下"),
            ("邓紫棋-喜欢你", "邓紫棋", "喜欢你"),
            ("方大同-特别的人", "方大同", "特别的人"),
            ("李健-贝加尔湖畔", "李健", "贝加尔湖畔"),
            ("李荣浩-模特", "李荣浩", "模特"),
            ("梁博-出现又离开", "梁博", "出现又离开"),
            ("林俊杰-不为谁而作的歌", "林俊杰", "不为谁而作的歌"),
            ("孙燕姿-我怀念的", "孙燕姿", "我怀念的"),
            (" 歌手- 歌曲 ", "歌手", "歌曲"),
            ("歌手 -歌曲", "歌手", "歌曲"),
            ("歌手-歌名-副标题", "歌手", "歌名-副标题"),
            ("AC-DC - Thunderstruck", "AC-DC", "Thunderstruck"),
            ("Beyond－情人", "Beyond", "情人"),
            ("陈奕迅—富士山下", "陈奕迅", "富士山下"),
            ("歌手 – 歌曲", "歌手", "歌曲"),
            ("歌手‑歌曲", "歌手", "歌曲"),
        ]
        for filename, artist, title in examples:
            with self.subTest(filename=filename):
                self.assertEqual(parse_filename(filename), (artist, title))

    def test_test_mode_never_persists(self):
        for _ in range(20):
            self.game.next()
            self.game.played()
            self.game.reveal()
        self.assertIsNone(self.store.active())
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM plays").fetchone()[0], 0)

    def test_selection_is_not_play_and_replay_is_idempotent(self):
        self.game.start()
        self.game.next()
        self.assertFalse(self.store.used(self.game.session_id))
        self.assertEqual(self.game.played(), 1)
        self.assertEqual(self.game.played(), 1)
        self.assertEqual(len(self.store.history(self.game.session_id)), 1)

    def test_cross_round_and_versions_excluded(self):
        self.game.start()
        self.game.current = self.a
        self.game.played()
        self.game.end_round()
        with self.assertRaises(ValueError):
            self.game.next()
        self.game.next_round()
        self.assertEqual(self.game.next().id, self.b.id)
        self.game.played()
        with self.assertRaises(ValueError):
            self.game.next()
        self.assertEqual(self.game.current.id, self.b.id)
        self.assertEqual(len(self.store.used(self.game.session_id)), 2)

    def test_crash_resume_and_new_activity(self):
        self.game.start()
        session_id = self.game.session_id
        self.game.current = self.a
        self.game.played()
        self.game.reveal()
        self.store.close()
        self.store = Store(self.tmp.name)
        self.game = Game(self.store, CONFIG)
        self.assertFalse(self.game.formal)
        self.game.resume()
        self.assertEqual(self.game.session_id, session_id)
        self.assertEqual(self.game.current.id, self.a.id)
        self.assertFalse(self.game.revealed)
        self.assertEqual(self.game.next().id, self.b.id)
        self.game.finish()
        self.game.start()
        self.assertFalse(self.store.used(self.game.session_id))
        self.assertTrue(self.store.history(session_id))
        snapshot = json.loads(self.game.session["config_json"])
        self.assertEqual(snapshot, CONFIG)

    def test_closed_round_resume_and_no_record(self):
        self.game.start()
        self.game.current = self.a
        self.game.played()
        self.game.end_round()
        resumed = Game(self.store, CONFIG)
        resumed.resume()
        self.assertIsNone(resumed.current)
        self.assertFalse(resumed.session["round_open"])
        with self.assertRaises(ValueError):
            self.store.record_play(resumed.session_id, self.b)
        resumed.next_round()
        self.assertEqual(resumed.session["round_no"], 2)

    def test_previous_hides_answer_and_does_not_duplicate(self):
        self.game.start()
        self.game.current = self.a
        self.game.played()
        self.game.next()
        self.game.played()
        self.game.reveal()
        self.game.previous()
        self.assertFalse(self.game.revealed)
        self.assertEqual(self.game.current.id, self.a.id)
        self.game.played()
        self.assertEqual(len(self.store.history(self.game.session_id)), 2)

    def test_manual_formal_selection_and_active_edit_rejected(self):
        self.game.start()
        with self.assertRaises(ValueError):
            self.game.select_code("1")
        with self.assertRaises(ValueError):
            self.store.edit_song(self.a.id, "A", "New", "")
        with self.assertRaises(ValueError):
            self.game.start()

    def test_empty_and_unknown_code(self):
        with self.assertRaises(ValueError):
            self.game.select_code("not a number")
        with self.assertRaises(ValueError):
            choose_song([], set())


if __name__ == "__main__":
    unittest.main()
