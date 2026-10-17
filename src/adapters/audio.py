"""A private audio stream: no media-session title or artwork publication."""
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame


class Audio:
    def __init__(self, volume=0.65):
        self.volume = volume
        self.paused = False
        self.loaded = False

    def play(self, path):
        self.stop()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            if not pygame.mixer.music.get_busy():
                raise RuntimeError("音频未启动。")
            self.loaded = True
        except Exception as exc:
            self.stop()
            raise RuntimeError("播放失败，请检查音频文件及系统声音输出设备。") from exc

    def toggle(self):
        if not self.loaded:
            return
        if self.paused:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()
        self.paused = not self.paused

    def stop(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        self.paused = False
        self.loaded = False

    def busy(self):
        return bool(pygame.mixer.get_init() and pygame.mixer.music.get_busy())

    def position(self):
        if not self.loaded or not pygame.mixer.get_init():
            return 0
        return max(0, pygame.mixer.music.get_pos())

    def set_volume(self, volume):
        self.volume = volume
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(volume)

    def close(self):
        self.stop()
        if pygame.mixer.get_init():
            pygame.mixer.quit()
