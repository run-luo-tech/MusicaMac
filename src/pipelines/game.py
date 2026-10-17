"""Activity lifecycle and question selection, independent of the GUI."""
from src.core.models import choose_song


class Game:
    def __init__(self, store, config):
        self.store, self.config = store, config
        self.session_id = None
        self.current = None
        self.revealed = False

    @property
    def formal(self):
        return self.session_id is not None

    @property
    def session(self):
        return self.store.session(self.session_id) if self.formal else None

    def clear(self):
        self.current = None
        self.revealed = False

    def start(self):
        if not self.store.songs():
            raise ValueError("请先在曲库管理中导入 MP3。")
        if self.store.active():
            raise ValueError("存在未完成活动，请恢复或结束它。")
        self.session_id = self.store.start(self.config)
        self.clear()

    def resume(self):
        active = self.store.active()
        if not active:
            raise ValueError("没有可恢复的活动。")
        self.session_id = active["id"]
        self.clear()
        history = self.store.history(self.session_id, active["round_no"])
        if history and active["round_open"]:
            self.current = self.store.song(history[-1]["song_id"])

    def next(self):
        if self.formal and not self.session["round_open"]:
            raise ValueError("请先开始下一轮。")
        used = self.store.used(self.session_id) if self.formal else set()
        # Choose before replacing current; exhaustion retains the last question.
        selected = choose_song(self.store.songs(), used, self.current.id if self.current else None)
        self.current, self.revealed = selected, False
        return selected

    def previous(self):
        if not self.formal or not self.session["round_open"]:
            raise ValueError("正式活动进行中才能回看本轮题目。")
        history = self.store.history(self.session_id, self.session["round_no"])
        ids = [p["song_id"] for p in history]
        if not ids:
            raise ValueError("本轮还没有已播放题目。")
        index = ids.index(self.current.id) if self.current and self.current.id in ids else len(ids)
        if index == 0:
            raise ValueError("已经是本轮第一题。")
        self.current = self.store.song(ids[index - 1])
        self.revealed = False

    def select_code(self, code):
        if self.formal:
            raise ValueError("正式活动请使用随机选题。")
        try:
            song = self.store.song(int(code))
        except (ValueError, TypeError):
            song = None
        if not song:
            raise ValueError("未找到该编号。")
        self.current, self.revealed = song, False

    def played(self):
        if not self.current:
            raise ValueError("请先选择题目。")
        if self.formal:
            return self.store.record_play(self.session_id, self.current)

    def reveal(self):
        if not self.current:
            raise ValueError("请先选择题目。")
        self.revealed = True

    def end_round(self):
        if not self.formal:
            raise ValueError("当前处于测试模式。")
        self.store.set_round(self.session_id, False)
        self.clear()

    def next_round(self):
        if not self.formal or self.session["round_open"]:
            raise ValueError("请先结束当前轮次。")
        self.store.set_round(self.session_id, True, advance=True)
        self.clear()

    def finish(self):
        if self.formal:
            self.store.finish(self.session_id)
        self.session_id = None
        self.clear()

    def status(self):
        if not self.formal:
            return "测试模式", "自由试听 · 不记录题目"
        session = self.session
        history = self.store.history(self.session_id, session["round_no"])
        played = next((p for p in history if self.current and p["song_id"] == self.current.id), None)
        index = played["ordinal"] if played else len(history) + 1
        detail = (f"第 {session['round_no']} 轮 · 第 {index} 题" if session["round_open"]
                  else f"第 {session['round_no']} 轮已结束 · 等待下一轮")
        return "正式活动", detail
