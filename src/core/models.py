"""Pure song identity and candidate rules."""
from dataclasses import dataclass
import random
import re


@dataclass(frozen=True)
class Song:
    id: int
    artist: str
    title: str
    version: str
    group_key: str
    duration: float

    @property
    def code(self):
        return f"{self.id:06d}"


def parse_filename(stem):
    # Recognize common dash glyphs copied from downloaded music filenames.
    # A spaced separator keeps hyphenated artist names (AC-DC - ...) intact.
    dashes = r"[-‐‑‒–—―−﹣－]"
    split = re.search(r"\s+" + dashes + r"\s+", stem)
    if split is None:
        split = re.search(dashes, stem)
    if split is None:
        return "", stem.strip()
    artist, title = stem[:split.start()], stem[split.end():]
    return artist.strip(), title.strip()


def group_key(artist, title):
    def normalize(s):
        return re.sub(r"\s+", " ", s.strip()).casefold()
    return normalize(artist) + "\x1f" + normalize(title)


def choose_song(songs, used, previous=None):
    candidates = [s for s in songs if s.group_key not in used]
    if not candidates:
        raise ValueError("本场可用歌曲已用完，请结束活动或补充曲库。")
    alternatives = [s for s in candidates if s.id != previous]
    return random.SystemRandom().choice(alternatives or candidates)
