"""A private audio stream: no media-session title or artwork publication."""
import os
import math
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame


class Audio:
    def __init__(self, volume=0.65):
        self.volume = volume
        self.paused = False
        self.loaded = False
        self.offset_ms = 0
        self.paused_position = 0

    def play(self, path, start=0):
        start = self.validate_position(start)
        self.stop()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(start=start)
            if not pygame.mixer.music.get_busy():
                raise RuntimeError("音频未启动。")
            self.loaded = True
            self.offset_ms = round(start * 1000)
        except Exception as exc:
            self.stop()
            raise RuntimeError("播放失败，请检查音频文件及系统声音输出设备。") from exc

    def toggle(self):
        if not self.loaded:
            return
        if self.paused:
            pygame.mixer.music.unpause()
        else:
            self.paused_position = self.position()
            pygame.mixer.music.pause()
        self.paused = not self.paused

    @staticmethod
    def validate_position(seconds):
        seconds = float(seconds)
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("播放位置无效。")
        return seconds

    def seek(self, seconds):
        seconds = self.validate_position(seconds)
        if not self.loaded:
            return
        remain_paused = self.paused or not self.busy()
        try:
            # Restarting at an absolute offset also resets get_pos's elapsed clock.
            pygame.mixer.music.play(start=seconds)
            if not pygame.mixer.music.get_busy():
                raise RuntimeError("音频未启动。")
            self.offset_ms = round(seconds * 1000)
            self.paused_position = self.offset_ms
            self.paused = remain_paused
            if remain_paused:
                pygame.mixer.music.pause()
        except Exception as exc:
            self.stop()
            raise RuntimeError("调整进度失败，请重新播放或检查 MP3。") from exc

    def stop(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        self.paused = False
        self.loaded = False
        self.offset_ms = 0
        self.paused_position = 0

    def busy(self):
        return bool(pygame.mixer.get_init() and pygame.mixer.music.get_busy())

    def position(self):
        if not self.loaded or not pygame.mixer.get_init():
            return 0
        if self.paused:
            return self.paused_position
        return self.offset_ms + max(0, pygame.mixer.music.get_pos())

    def set_volume(self, volume):
        self.volume = volume
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(volume)

    def close(self):
        self.stop()
        if pygame.mixer.get_init():
            pygame.mixer.quit()
