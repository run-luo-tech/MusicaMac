"""Transactional local library and activity history."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from src.core.models import Song, group_key


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "audio").mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.directory / "library.db")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS songs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          artist TEXT NOT NULL, title TEXT NOT NULL, version TEXT NOT NULL,
          group_key TEXT NOT NULL, duration REAL NOT NULL,
          sha256 TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL,
          ended_at TEXT, round_no INTEGER NOT NULL DEFAULT 1,
          round_open INTEGER NOT NULL DEFAULT 1, config_json TEXT NOT NULL);
        CREATE UNIQUE INDEX IF NOT EXISTS single_active_session
          ON sessions((1)) WHERE ended_at IS NULL;
        CREATE TABLE IF NOT EXISTS plays (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id INTEGER NOT NULL REFERENCES sessions(id),
          round_no INTEGER NOT NULL, song_id INTEGER NOT NULL REFERENCES songs(id),
          group_key TEXT NOT NULL, ordinal INTEGER NOT NULL,
          played_at TEXT NOT NULL, UNIQUE(session_id, group_key));
        PRAGMA user_version=1;
        """)

    def close(self):
        self.db.close()

    def songs(self):
        return [Song(**dict(r)) for r in self.db.execute(
            "SELECT id,artist,title,version,group_key,duration FROM songs ORDER BY id")]

    def song(self, song_id):
        return next((s for s in self.songs() if s.id == song_id), None)

    def audio_path(self, song_id):
        return self.directory / "audio" / f"{song_id:06d}.mp3"

    def active(self):
        row = self.db.execute("SELECT * FROM sessions WHERE ended_at IS NULL").fetchone()
        return dict(row) if row else None

    def session(self, session_id):
        row = self.db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else None

    def start(self, config):
        with self.db:
            result = self.db.execute("INSERT INTO sessions(started_at,config_json) VALUES (?,?)",
                                     (now(), json.dumps(config, ensure_ascii=False)))
        return result.lastrowid

    def set_round(self, session_id, opened, advance=False):
        with self.db:
            self.db.execute("UPDATE sessions SET round_open=?,round_no=round_no+? "
                            "WHERE id=? AND ended_at IS NULL",
                            (int(opened), int(advance), session_id))

    def finish(self, session_id):
        with self.db:
            self.db.execute("UPDATE sessions SET ended_at=?,round_open=0 WHERE id=?",
                            (now(), session_id))

    def used(self, session_id):
        return {r[0] for r in self.db.execute(
            "SELECT group_key FROM plays WHERE session_id=?", (session_id,))}

    def history(self, session_id, round_no=None):
        query = "SELECT * FROM plays WHERE session_id=?"
        params = [session_id]
        if round_no is not None:
            query += " AND round_no=?"
            params.append(round_no)
        return [dict(r) for r in self.db.execute(query + " ORDER BY id", params)]

    def record_play(self, session_id, song):
        with self.db:
            session = self.session(session_id)
            if not session or session["ended_at"] or not session["round_open"]:
                raise ValueError("本轮尚未开始。")
            old = self.db.execute("SELECT * FROM plays WHERE session_id=? AND group_key=?",
                                  (session_id, song.group_key)).fetchone()
            if old:
                if old["song_id"] != song.id or old["round_no"] != session["round_no"]:
                    raise ValueError("这首歌曲本场已使用，请切换题目。")
                return old["ordinal"]
            ordinal = len(self.history(session_id, session["round_no"])) + 1
            self.db.execute("INSERT INTO plays(session_id,round_no,song_id,group_key,ordinal,played_at) "
                            "VALUES (?,?,?,?,?,?)", (session_id, session["round_no"], song.id,
                                                    song.group_key, ordinal, now()))
        return ordinal

    def edit_song(self, song_id, artist, title, version):
        if self.active():
            raise ValueError("请先结束未完成活动，再修改曲库答案。")
        artist, title, version = artist.strip(), title.strip(), version.strip()
        if not artist or not title:
            raise ValueError("歌手和歌曲名不能为空。")
        with self.db:
            self.db.execute("UPDATE songs SET artist=?,title=?,version=?,group_key=? WHERE id=?",
                            (artist, title, version, group_key(artist, title), song_id))
