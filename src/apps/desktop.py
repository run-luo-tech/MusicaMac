"""Shared-screen guessing UI; answers exist visibly only after reveal."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from src.core.models import parse_filename
from src.adapters.audio import Audio
from src.adapters.library import Library
from src.pipelines.game import Game

APP_VERSION = "0.2.0"
FONT_FAMILY = "PingFang SC"
BG = "#FFF7ED"
CARD = "#FFFFFF"
FG = "#302543"
MUTED = "#786A85"
ACCENT = "#7C3AED"
CORAL = "#D94B34"


def label(parent, text="", size=11, color=FG, **kwargs):
    return tk.Label(parent, text=text, font=(FONT_FAMILY, size),
                    fg=color, bg=parent.cget("bg"), **kwargs)


def button(parent, text, command, style="TButton", **kwargs):
    return ttk.Button(parent, text=text, command=command, style=style, **kwargs)


class Desktop:
    def __init__(self, root, store, config):
        self.root, self.store = root, store
        self.game = Game(store, config)
        self.library = Library(store)
        self.audio = Audio(config["volume"])
        self.management = None
        self.message = "先导入 MP3，再导出手机答案表。测试播放不会记录题目。"
        root.title(f"Musica · 听歌猜曲 v{APP_VERSION}")
        root.geometry("1120x780")
        root.minsize(940, 720)
        root.configure(bg=BG)
        self.style()
        self.build()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<F11>", lambda e: self.fullscreen())
        root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
        root.after(250, self.tick)
        self.render()

    def style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TButton", font=(FONT_FAMILY, 11), padding=(15, 11),
                        background="#EDE4FF", foreground="#59328E", borderwidth=0)
        style.map("TButton", background=[("disabled", "#F0EAEF"), ("active", "#DDCCFF")],
                  foreground=[("disabled", "#9C8FA3")])
        for name, bg, fg, hover in [("Accent", ACCENT, "#FFFFFF", "#6526D1"),
                                    ("Gold", "#FFB84D", "#542E08", "#FFA326")]:
            style.configure(name + ".TButton", background=bg, foreground=fg)
            style.map(name + ".TButton", background=[("disabled", "#F0EAEF"), ("active", hover)],
                      foreground=[("disabled", "#9C8FA3"), ("active", fg)])
        style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=FG,
                        rowheight=34, font=(FONT_FAMILY, 10), borderwidth=0)
        style.configure("Treeview.Heading", background="#EDE4FF", foreground="#59328E",
                        font=(FONT_FAMILY, 10), padding=8)
        style.map("Treeview", background=[("selected", "#E5D6FF")], foreground=[("selected", "#432071")])
        style.configure("TEntry", fieldbackground="#FFFFFF", foreground=FG,
                        bordercolor="#D9C7F1", lightcolor="#D9C7F1", darkcolor="#D9C7F1", padding=6)
        style.configure("Vertical.TScrollbar", background="#D7C5F3", troughcolor="#F7F1FD",
                        arrowcolor="#765294", borderwidth=0)
        style.configure("Horizontal.TScale", background=CARD, troughcolor="#EDE4FF", borderwidth=0)
        style.configure("Horizontal.TProgressbar", background="#FF946D", troughcolor="#F1E9FC",
                        borderwidth=0, thickness=5)

    def build(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=34, pady=24)
        top = tk.Frame(outer, bg=BG)
        top.pack(fill="x")
        label(top, "MUSICA", 22, ACCENT, anchor="w").pack(side="left")
        label(top, f"听歌猜曲  /  v{APP_VERSION}", 12, MUTED).pack(side="left", padx=14)
        button(top, "全屏  F11", self.fullscreen).pack(side="right")
        self.manage_button = button(top, "曲库管理 / 导出答案", self.manage)
        self.manage_button.pack(side="right", padx=10)

        bar = tk.Frame(outer, bg=BG)
        bar.pack(fill="x", pady=(22, 14))
        self.mode = label(bar, size=12, color=ACCENT)
        self.mode.pack(side="left")
        self.count = label(bar, size=10, color=MUTED)
        self.count.pack(side="right")

        card = tk.Frame(outer, bg=CARD, padx=30, pady=20)
        card.pack(fill="both", expand=True)
        self.round_label = label(card, size=13, color=MUTED)
        self.round_label.pack(pady=(0, 5))
        label(card, "歌曲编号", 11, MUTED).pack()
        self.code = label(card, "——", 24, ACCENT)
        self.code.configure(font=("Menlo", 24, "bold"))
        self.code.pack(pady=(0, 12))
        self.answer = label(card, "等待选题", 23, FG, wraplength=820)
        self.answer.pack(pady=(0, 4))
        self.artist = label(card, "主持人通过手机答案表查询对应编号", 11, MUTED, wraplength=820)
        self.artist.pack(pady=(0, 12))
        controls = tk.Frame(card, bg=CARD)
        controls.pack(pady=8)
        self.play_button = button(controls, "播放", self.play, "Accent.TButton", width=13)
        self.play_button.pack(side="left", padx=6)
        self.replay_button = button(controls, "重新播放", self.replay, width=12)
        self.replay_button.pack(side="left", padx=6)
        self.reveal_button = button(controls, "揭晓答案", self.reveal, "Gold.TButton", width=13)
        self.reveal_button.pack(side="left", padx=6)
        navigation = tk.Frame(card, bg=CARD)
        navigation.pack(pady=(5, 8))
        self.previous_button = button(navigation, "上一题（回看）", self.previous)
        self.previous_button.pack(side="left", padx=6)
        self.next_button = button(navigation, "随机下一题 →", self.next)
        self.next_button.pack(side="left", padx=6)
        self.code_button = button(navigation, "按编号测试", self.select_code)
        self.code_button.pack(side="left", padx=6)
        self.progress = ttk.Progressbar(card, mode="determinate")
        self.progress.pack(fill="x", pady=(10, 4))
        audio_bar = tk.Frame(card, bg=CARD)
        audio_bar.pack(fill="x")
        self.clock = label(audio_bar, "00:00 / 00:00", 10, MUTED)
        self.clock.pack(side="left")
        self.volume = tk.DoubleVar(value=self.audio.volume * 100)
        ttk.Scale(audio_bar, from_=0, to=100, variable=self.volume,
                  command=lambda v: self.audio.set_volume(float(v) / 100), length=130).pack(side="right")
        label(audio_bar, "音量", 10, MUTED).pack(side="right", padx=8)

        activity = tk.Frame(outer, bg=BG)
        activity.pack(fill="x", pady=(17, 10))
        self.start_button = button(activity, "正式开始", self.start, "Accent.TButton")
        self.start_button.pack(side="left")
        self.round_button = button(activity, "结束本轮", self.round_action)
        self.round_button.pack(side="left", padx=10)
        self.finish_button = button(activity, "结束活动", self.finish)
        self.finish_button.pack(side="left")
        self.restore_button = button(activity, "恢复未完成活动", self.resume)
        self.restore_button.pack(side="right")
        self.notice = label(outer, size=10, color=MUTED, anchor="w", wraplength=1010, justify="left")
        self.notice.pack(fill="x", pady=(3, 0))

    def fullscreen(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def set_message(self, text):
        self.message = text
        self.notice.config(text=text)

    def render(self):
        formal = self.game.formal
        session = self.game.session
        round_open = not formal or bool(session["round_open"])
        song = self.game.current
        mode, detail = self.game.status()
        self.mode.config(text="● " + mode, fg=CORAL if formal else ACCENT)
        self.round_label.config(text=detail)
        self.code.config(text=song.code if song else "——")
        if song and self.game.revealed:
            self.answer.config(text=song.title, font=(FONT_FAMILY, 38, "bold"))
            self.artist.config(text=song.artist + ("  ·  " + song.version if song.version else ""),
                               font=(FONT_FAMILY, 23), fg=ACCENT)
        else:
            self.answer.config(text="等待揭晓" if song else ("本轮已结束" if not round_open else "准备好，听下一首"),
                               font=(FONT_FAMILY, 23))
            self.artist.config(text="主持人通过手机答案表查询对应编号",
                               font=(FONT_FAMILY, 11), fg=MUTED)
        songs = self.store.songs()
        available = len({s.group_key for s in songs} - (self.store.used(self.game.session_id) if formal else set()))
        self.count.config(text=f"曲库 {len(songs)} 首   ·   本场剩余 {available} 组" if formal else f"曲库 {len(songs)} 首")
        state = lambda enabled: "normal" if enabled else "disabled"
        self.manage_button.config(state=state(not formal))
        self.start_button.config(state=state(not formal and not self.store.active() and bool(songs)))
        self.restore_button.config(state=state(not formal and bool(self.store.active())))
        self.round_button.config(state=state(formal), text="结束本轮" if round_open else "开始下一轮")
        self.finish_button.config(state=state(formal))
        self.code_button.config(state=state(not formal))
        self.previous_button.config(state=state(formal and round_open))
        self.next_button.config(state=state(round_open and bool(songs)))
        for widget in (self.play_button, self.replay_button, self.reveal_button):
            widget.config(state=state(song is not None and round_open))
        self.notice.config(text=self.message)
        self.refresh_player()

    def attempt(self, action):
        try:
            action()
        except ValueError as exc:
            self.set_message(str(exc))
        except Exception:
            self.audio.stop()
            self.set_message("操作未完成，请检查曲库目录是否可写，或重启后恢复活动。")
        self.render()

    def next(self):
        self.audio.stop()
        self.game.revealed = False
        self.attempt(lambda: (self.game.next(), self.set_message("题目已就绪，点击播放。尚未播放不计入已用题目。")))

    def previous(self):
        self.audio.stop()
        self.game.revealed = False
        self.attempt(lambda: (self.game.previous(), self.set_message("回看本轮已用题目；重播不会增加计数。")))

    def select_code(self):
        code = simpledialog.askstring("按编号测试", "输入歌曲编号（例如 000001）：", parent=self.root)
        if code is not None:
            self.audio.stop()
            self.game.revealed = False
            self.attempt(lambda: self.game.select_code(code))

    def play(self):
        if self.audio.loaded and (self.audio.busy() or self.audio.paused):
            self.audio.toggle()
            self.refresh_player()
        else:
            self.begin_playback()

    def replay(self):
        self.begin_playback()

    def begin_playback(self):
        if not self.game.current:
            return
        try:
            self.audio.play(self.store.audio_path(self.game.current.id))
            self.game.played()
            self.set_message("正式播放已记录；本场后续选题会排除此歌曲组。" if self.game.formal else "正在测试播放，不记录已用题目。")
        except Exception:
            self.audio.stop()
            self.set_message(f"编号 {self.game.current.code} 播放未完成。请检查 MP3、声音设备或曲库写入权限；未确认成功的新题不会计入记录。")
        self.render()

    def reveal(self):
        self.attempt(self.game.reveal)

    def start(self):
        self.audio.stop()
        self.game.clear()
        self.attempt(lambda: (self.game.start(), self.set_message("正式活动已开始。点击随机下一题，再点击播放。")))

    def resume(self):
        self.audio.stop()
        self.attempt(lambda: (self.game.resume(), self.set_message("已恢复活动和跨轮使用记录；上次答案已隐藏。")))

    def round_action(self):
        if not self.game.formal:
            return
        if self.game.session["round_open"]:
            if not messagebox.askyesno("结束本轮", "结束当前轮次？已用歌曲会保留到本场活动结束。", parent=self.root):
                return
            self.audio.stop()
            self.attempt(lambda: (self.game.end_round(), self.set_message("本轮已结束，可以开始下一轮。")))
        else:
            self.attempt(lambda: (self.game.next_round(), self.set_message("新一轮已开始，前面各轮的歌曲仍会排除。")))

    def finish(self):
        if messagebox.askyesno("结束活动", "确定结束整场活动？历史将保存，界面回到测试模式。", parent=self.root):
            self.audio.stop()
            self.attempt(lambda: (self.game.finish(), self.set_message("活动已结束。当前为测试模式，下次正式开始将创建新活动。")))

    def manage(self):
        if self.game.formal:
            return
        if self.store.active():
            self.set_message("存在未完成活动。请先恢复并结束活动，再修改曲库；可先导出已有答案。")
        self.audio.stop()
        self.game.clear()
        self.render()
        self.management = LibraryDialog(self)
        self.root.wait_window(self.management.window)
        self.management = None
        self.render()

    def refresh_player(self):
        self.play_button.config(text="继续播放" if self.audio.paused else "暂停" if self.audio.busy() else "播放")
        duration = self.game.current.duration if self.game.current else 0
        pos = min(self.audio.position() / 1000, duration)
        if self.audio.loaded and not self.audio.paused and not self.audio.busy():
            pos = duration
        self.progress.config(maximum=max(1, duration), value=pos)
        fmt = lambda v: f"{int(v)//60:02d}:{int(v)%60:02d}"
        self.clock.config(text=f"{fmt(pos)} / {fmt(duration)}")

    def tick(self):
        self.refresh_player()
        self.root.after(250, self.tick)

    def close(self):
        if self.game.formal and not messagebox.askyesno("退出 Musica", "活动尚未结束。退出后记录会保留，下次可恢复。现在退出？", parent=self.root):
            return
        self.audio.close()
        self.store.close()
        self.root.destroy()


class LibraryDialog:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title(f"Musica v{APP_VERSION} · 曲库管理（含答案）")
        self.window.geometry("1000x650")
        self.window.minsize(850, 580)
        self.window.configure(bg=BG)
        self.window.transient(app.root)
        self.window.grab_set()
        outer = tk.Frame(self.window, bg=BG, padx=22, pady=18)
        outer.pack(fill="both", expand=True)
        label(outer, "曲库管理", 19, ACCENT).pack(anchor="w")
        label(outer, "此窗口包含答案。导入后请重新导出手机答案表。", 10, MUTED).pack(anchor="w", pady=(5, 14))
        bar = tk.Frame(outer, bg=BG)
        bar.pack(fill="x", pady=(0, 14))
        importing = button(bar, "批量导入 MP3", self.import_files, "Accent.TButton")
        importing.pack(side="left")
        folder = button(bar, "导入文件夹", self.import_folder)
        folder.pack(side="left", padx=8)
        button(bar, "导出手机答案表", self.export_html).pack(side="right")
        button(bar, "导出 CSV", self.export_csv).pack(side="right", padx=8)
        if app.store.active():
            importing.config(state="disabled")
            folder.config(state="disabled")
        table_frame = tk.Frame(outer, bg=BG)
        table_frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_frame, columns=("code", "artist", "title", "version", "duration"), show="headings", selectmode="browse")
        for name, text, width in [("code", "编号", 90), ("artist", "歌手", 160), ("title", "歌曲名", 300), ("version", "版本备注", 160), ("duration", "时长", 70)]:
            self.table.heading(name, text=text)
            self.table.column(name, width=width, minwidth=60)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)
        editor = tk.Frame(outer, bg=BG)
        editor.pack(fill="x", pady=14)
        self.fields = {}
        for name, title in [("artist", "歌手"), ("title", "歌曲名"), ("version", "版本备注")]:
            cell = tk.Frame(editor, bg=BG)
            cell.pack(side="left", fill="x", expand=True, padx=(0, 10))
            label(cell, title, 10, MUTED).pack(anchor="w")
            var = tk.StringVar()
            ttk.Entry(cell, textvariable=var, font=(FONT_FAMILY, 11)).pack(fill="x", pady=5)
            self.fields[name] = var
        self.save_button = button(editor, "保存答案修改", self.edit)
        self.save_button.pack(side="right", pady=(16, 0))
        if app.store.active():
            self.save_button.config(state="disabled")
        self.status = label(outer, "选中歌曲可修改答案；修改后编号不变。", 10, MUTED, wraplength=900, anchor="w")
        self.status.pack(fill="x")
        self.table.bind("<<TreeviewSelect>>", self.selection)
        self.reload()

    def reload(self):
        self.table.delete(*self.table.get_children())
        for s in self.app.store.songs():
            self.table.insert("", "end", iid=str(s.id), values=(s.code, s.artist, s.title, s.version, f"{int(s.duration)//60}:{int(s.duration)%60:02d}"))

    def selection(self, event=None):
        selected = self.table.selection()
        if selected:
            song = self.app.store.song(int(selected[0]))
            for field, var in self.fields.items():
                var.set(getattr(song, field))

    def edit(self):
        if not self.table.selection():
            return
        try:
            self.app.store.edit_song(int(self.table.selection()[0]), *(v.get() for v in self.fields.values()))
            self.reload()
            self.status.config(text="答案已保存，请重新导出手机答案表。")
        except ValueError as exc:
            self.status.config(text=str(exc))
        except Exception:
            self.status.config(text="保存失败，请检查曲库目录写入权限。")

    def import_files(self):
        files = filedialog.askopenfilenames(parent=self.window, title="选择 MP3（可多选）", filetypes=[("MP3 音频", "*.mp3")])
        self.import_preview(files)

    def import_folder(self):
        folder = filedialog.askdirectory(parent=self.window, title="选择 MP3 文件夹（包含子文件夹）")
        if folder:
            self.import_preview(sorted(p for p in Path(folder).rglob("*") if p.is_file() and p.suffix.lower() == ".mp3"))

    def import_preview(self, files):
        if not files:
            return
        dialog = ImportDialog(self, files)
        self.window.wait_window(dialog.window)
        self.window.grab_set()
        self.reload()

    def export_html(self):
        self.export("html", self.app.library.export_html)

    def export_csv(self):
        self.export("csv", self.app.library.export_csv)

    def export(self, suffix, action):
        if not self.app.store.songs():
            self.status.config(text="曲库为空，请先导入 MP3。")
            return
        target = filedialog.asksaveasfilename(parent=self.window, title="导出主持人答案表", initialfile="Musica 主持人答案表." + suffix,
                                            defaultextension="." + suffix, filetypes=[(suffix.upper(), "*." + suffix)])
        if target:
            try:
                action(target)
                self.status.config(text="已导出。请把答案表传到主持人手机上查看。")
            except Exception:
                self.status.config(text="导出失败，请选择可写入的位置。")


class ImportDialog:
    def __init__(self, parent, files):
        self.parent = parent
        self.window = tk.Toplevel(parent.window)
        self.window.title(f"导入预览 v{APP_VERSION} · 自动读取 MP3 文件名")
        self.window.geometry("1060x650")
        self.window.configure(bg=BG)
        self.window.transient(parent.window)
        self.window.grab_set()
        self.rows = []
        for path in files:
            path = Path(path)
            artist, title = parse_filename(path.stem)
            self.rows.append({"path": path, "artist": artist, "title": title, "version": "", "status": "待导入" if artist and title else "需补全歌手/歌名", "done": False})
        self.selected = None
        self.running = False
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        outer = tk.Frame(self.window, bg=BG, padx=20, pady=18)
        outer.pack(fill="both", expand=True)
        label(outer, "检查答案，再导入", 19, ACCENT).pack(anchor="w")
        label(outer, "自动读取文件名：歌手-歌曲名.mp3（也支持带空格）。选中一行可修改，切换行自动保存；原文件不变。", 10, MUTED).pack(anchor="w", pady=(8, 15))
        area = tk.Frame(outer, bg=BG)
        area.pack(fill="both", expand=True)
        self.table = ttk.Treeview(area, columns=("file", "artist", "title", "version", "status"), show="headings", selectmode="browse")
        for name, title, width in [("file", "原文件名", 250), ("artist", "歌手", 140), ("title", "歌曲名", 220), ("version", "版本备注", 120), ("status", "状态", 230)]:
            self.table.heading(name, text=title)
            self.table.column(name, width=width, minwidth=70)
        scroll = ttk.Scrollbar(area, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)
        for i in range(len(self.rows)):
            self.table.insert("", "end", iid=str(i), values=self.values(i))
        editor = tk.Frame(outer, bg=BG)
        editor.pack(fill="x", pady=15)
        self.fields = {}
        self.entries = []
        for key, title in [("artist", "歌手"), ("title", "歌曲名"), ("version", "版本备注")]:
            frame = tk.Frame(editor, bg=BG)
            frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
            label(frame, title, 10, MUTED).pack(anchor="w")
            variable = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=variable, font=(FONT_FAMILY, 11))
            entry.pack(fill="x", pady=6)
            self.entries.append(entry)
            self.fields[key] = variable
        bottom = tk.Frame(outer, bg=BG)
        bottom.pack(fill="x")
        self.import_button = button(bottom, "确认导入", self.begin, "Accent.TButton")
        self.import_button.pack(side="right")
        self.close_button = button(bottom, "关闭", self.close)
        self.close_button.pack(side="right", padx=8)
        self.status = label(bottom, f"共 {len(self.rows)} 个文件。请补全缺失答案后导入。", 10, MUTED, wraplength=650)
        self.status.pack(side="left")
        self.table.bind("<<TreeviewSelect>>", self.select)
        self.table.selection_set("0")

    def values(self, i):
        r = self.rows[i]
        return r["path"].name, r["artist"], r["title"], r["version"], r["status"]

    def flush(self):
        if self.selected is not None and not self.rows[self.selected]["done"]:
            r = self.rows[self.selected]
            changed = any(r[key] != var.get().strip() for key, var in self.fields.items())
            for key, var in self.fields.items():
                r[key] = var.get().strip()
            if changed:
                r["status"] = "待导入" if r["artist"] and r["title"] else "需补全歌手/歌名"
            self.table.item(str(self.selected), values=self.values(self.selected))

    def select(self, event=None):
        if self.running:
            return
        self.flush()
        selected = self.table.selection()
        self.selected = int(selected[0]) if selected else None
        if self.selected is not None:
            r = self.rows[self.selected]
            for key, var in self.fields.items():
                var.set(r[key])
            for entry in self.entries:
                entry.config(state="disabled" if r["done"] else "normal")

    def begin(self):
        self.flush()
        pending = [r for r in self.rows if not r["done"]]
        if not pending:
            self.status.config(text="全部处理完毕，可以关闭窗口。")
            return
        if any(not r["artist"] or not r["title"] for r in pending):
            self.status.config(text="请先补全所有待导入行的歌手和歌曲名。")
            return
        self.running = True
        self.import_button.config(state="disabled")
        self.close_button.config(state="disabled")
        for entry in self.entries:
            entry.config(state="disabled")
        self.process(0)

    def process(self, index):
        if index >= len(self.rows):
            self.running = False
            self.import_button.config(state="normal")
            self.close_button.config(state="normal")
            count = sum(r["done"] for r in self.rows)
            self.status.config(text=f"已处理 {count}/{len(self.rows)} 行；失败行可修改后重试。完成后请重新导出答案表。")
            if self.selected is not None:
                for entry in self.entries:
                    entry.config(state="disabled" if self.rows[self.selected]["done"] else "normal")
            return
        row = self.rows[index]
        if not row["done"]:
            try:
                code, added = self.parent.app.library.import_mp3(row["path"], row["artist"], row["title"], row["version"])
                row["status"] = ("已导入 " if added else "重复文件，跳过 ") + f"{code:06d}"
                row["done"] = True
            except ValueError as exc:
                row["status"] = str(exc)
            except Exception:
                row["status"] = "导入失败，请检查文件读取和曲库写入权限"
            self.table.item(str(index), values=self.values(index))
            self.table.see(str(index))
        self.status.config(text=f"处理中 {index + 1}/{len(self.rows)}…")
        self.window.after(10, lambda: self.process(index + 1))

    def close(self):
        if not self.running:
            self.window.destroy()
