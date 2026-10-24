# Musica Logo

用户提供的 Musica_logo.png 为原始图稿，保持原样。logo-80.png 用于主界面，logo-256.png 用于窗口图标；Musica.ico 用于 Windows EXE/安装器，Musica.icns 用于 Mac app/Finder/Dock。

派生文件只做等比缩放及图标格式转换，不重绘、不裁切或改动配色。安装包内置资源，运行时无需原文件或联网。需要重生成时，在安装 Pillow 的维护环境运行 `python scripts/prepare_branding.py`；普通使用和打包直接使用已提交的资源。
