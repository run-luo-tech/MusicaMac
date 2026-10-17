# 第三方组件

本程序使用 Python（PSF License）、Tcl/Tk（Tcl/Tk License）、SQLite（public domain）、pygame-ce（LGPL-2.1）和 mutagen（GPL-2.0-or-later）。打包器 PyInstaller 使用 GPL 及其 bootloader exception。

依赖版本见 requirements.txt 和 requirements-build.txt；pygame-ce 自带 SDL 等媒体组件，其许可文件随 wheel 及 PyInstaller 包保留。组件上游：

- https://github.com/pygame-community/pygame-ce
- https://github.com/quodlibet/mutagen
- https://www.python.org/psf/license/
- https://www.tcl.tk/software/tcltk/license.html
- https://www.sqlite.org/copyright.html
- https://pyinstaller.org/en/stable/license.html

Musica 第一版源代码在本项目根目录；独立程序分发时请同时提供对应源代码、依赖版本和组件许可。本项目尚未指定自有源代码的额外授权条款。
