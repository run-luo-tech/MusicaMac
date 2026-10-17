"""MP3 import and offline host answer sheets."""
import csv
import hashlib
from html import escape
from pathlib import Path
import shutil
from mutagen.mp3 import MP3
from mutagen.id3 import delete as delete_id3
from src.core.models import group_key
from src.adapters.store import now


class Library:
    def __init__(self, store):
        self.store = store

    def import_mp3(self, source, artist, title, version=""):
        source = Path(source)
        if source.suffix.lower() != ".mp3":
            raise ValueError("只支持 MP3 文件。")
        artist, title, version = artist.strip(), title.strip(), version.strip()
        if not artist or not title:
            raise ValueError("请补全歌手和歌曲名。")
        if self.store.active():
            raise ValueError("请先结束未完成活动，再导入歌曲。")
        try:
            duration = MP3(source).info.length
            if duration <= 0:
                raise ValueError()
        except Exception as exc:
            raise ValueError("不是可读取的 MP3 音频。") from exc
        with source.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        existing = self.store.db.execute("SELECT id FROM songs WHERE sha256=?", (digest,)).fetchone()
        if existing:
            return existing[0], False
        duplicate = self.store.db.execute(
            "SELECT id FROM songs WHERE group_key=? AND version=?",
            (group_key(artist, title), version)).fetchone()
        if duplicate:
            raise ValueError(f"同名版本已存在（{duplicate[0]:06d}），请填写不同的版本备注。")
        target = None
        try:
            with self.store.db:
                row = self.store.db.execute(
                    "INSERT INTO songs(artist,title,version,group_key,duration,sha256,created_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (artist, title, version, group_key(artist, title), duration, digest, now()))
                song_id = row.lastrowid
                target = self.store.audio_path(song_id)
                shutil.copyfile(source, target)
                delete_id3(target, delete_v1=True, delete_v2=True)
            return song_id, True
        except Exception:
            if target and target.exists():
                target.unlink()
            raise

    def export_csv(self, destination):
        with Path(destination).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["歌曲编号", "歌手", "歌曲名", "版本备注"])
            for s in self.store.songs():
                # Prevent a spreadsheet from treating imported text as a formula.
                safe = lambda v: "'" + v if v.startswith(("=", "+", "-", "@")) else v
                writer.writerow([s.code, safe(s.artist), safe(s.title), safe(s.version)])

    def export_html(self, destination):
        songs = self.store.songs()
        rows = "\n".join(
            "<tr><td>" + "</td><td>".join(escape(v) for v in
            (s.code, s.artist, s.title, s.version)) + "</td></tr>" for s in songs)
        document = """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Musica 主持人答案表</title><style>
body{font:16px system-ui,sans-serif;margin:0;padding:22px;background:#101827;color:#edf3fa}
h1{font-size:23px;margin:0 0 8px}p{color:#a8bbd1;line-height:1.6}
input{box-sizing:border-box;width:100%;padding:14px;border-radius:10px;border:1px solid #4b637d;
background:#1b2b40;color:white;font-size:18px}header{position:sticky;top:0;background:#101827;padding:14px 0}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;margin-top:14px}
td,th{text-align:left;padding:14px 10px;border-bottom:1px solid #304057}td:first-child{color:#63dece;font-weight:700;font-variant-numeric:tabular-nums}
th{white-space:nowrap;color:#b6c9df}small{color:#a8bbd1}</style>
<h1>Musica · 主持人答案表</h1><p>包含答案，请仅在主持人的手机上查看。<br>编号为曲库永久编号，与电脑屏幕对应。</p>
<small>__DATE__ · 共 __COUNT__ 首</small>
<header><input id="q" type="search" inputmode="search" placeholder="输入编号、歌手或歌名" aria-label="搜索答案"></header>
<div class="scroll"><table><thead><tr><th>编号</th><th>歌手</th><th>歌曲名</th><th>版本</th></tr></thead>
<tbody>__ROWS__</tbody></table></div><p id="empty" hidden>未找到对应歌曲。</p>
<script>const rows=[...document.querySelectorAll('tbody tr')];
document.querySelector('#q').addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();let n=0;
rows.forEach(r=>{r.hidden=!r.textContent.toLowerCase().includes(q);if(!r.hidden)n++});document.querySelector('#empty').hidden=n!==0;});</script></html>"""
        document = document.replace("__DATE__", now()).replace("__COUNT__", str(len(songs))).replace("__ROWS__", rows)
        Path(destination).write_text(document, encoding="utf-8")
