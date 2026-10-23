"""macOS entry: writable data live outside the app bundle."""
import json
import argparse
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox
from src.adapters.store import Store
from src.apps.desktop import Desktop, APP_VERSION

DEFAULT = {"schema_version": 1, "volume": 0.65, "selection": "random", "version": APP_VERSION}


def application_home():
    return Path.home() / "Library" / "Application Support" / "MusicaMac"


def load_config(home):
    path = home / "config" / "app.json"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(DEFAULT, indent=2), encoding="utf-8")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if (value.get("schema_version") != 1 or value.get("selection") != "random"
            or not isinstance(value.get("volume"), (int, float))
            or isinstance(value.get("volume"), bool) or not 0 <= value["volume"] <= 1):
        raise ValueError("配置格式错误。")
    value["version"] = APP_VERSION
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-report", type=Path, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("MusicaMac 启动入口仅用于 macOS；通用功能可在其他平台测试。")
    import fcntl
    home = application_home()
    home.mkdir(parents=True, exist_ok=True)
    lock = (home / "instance.lock").open("a+")
    root = tk.Tk()
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        root.withdraw()
        messagebox.showinfo("MusicaMac", "MusicaMac 已在运行，请切换到已有窗口。")
        root.destroy()
        lock.close()
        return
    try:
        app = Desktop(root, Store(home / "data"), load_config(home))
        root.bind("<Command-q>", lambda event: app.close())
        if arguments.smoke_report:
            root.after(500, lambda: smoke_test(app, arguments.smoke_report))
        root.mainloop()
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


def smoke_test(app, report):
    """Build-only probe: exercise the shipped Tk/MP3 stack on an isolated HOME."""
    result = {"version": APP_VERSION, "success": False}
    try:
        assert app.progress.winfo_class() == "TScale"
        app.game.select_code("000001")
        app.render()
        app.commit_seek(0.6)
        assert not app.audio.loaded and app.pending_position == 0.6
        app.begin_playback()
        assert app.audio.loaded and app.audio.busy()
        app.commit_seek(1.2)
        assert 1200 <= app.audio.position() < 1600
        app.play()
        app.commit_seek(0.4)
        assert app.audio.paused and app.audio.position() == 400
        app.play()
        assert app.audio.busy()
        assert app.game.current.title not in app.answer.cget("text")
        result.update(success=True, window=app.root.title(),
                      checks=["Tk slider", "MP3 playback", "absolute seek", "paused seek", "hidden answer"])
    except Exception as exc:
        result["error"] = repr(exc)
    finally:
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        app.audio.close()
        app.store.close()
        app.root.destroy()


if __name__ == "__main__":
    main()
