# 运行与维护环境

普通用户：自包含 .app，不需要 Python 或第三方播放器。构建目标：Apple Silicon/Intel 分开；系统最低版本需经对应架构实际打包验证，不能跨系统生成。

源码路径：scripts/environment.sh 从 https://astral.sh/uv/install.sh 安装项目私有 uv，再安装 managed Python 3.12、pygame-ce 2.5.8 和 mutagen 1.48.1。使用二进制 wheels，避免现场编译依赖。脚本不使用 sudo，不修改系统 Python/PATH/shell profile。初次下载需访问 astral.sh、GitHub/Python 发行资源和 PyPI；失败保留错误提示，恢复网络后重试。

维护者“生成Mac应用.command”额外安装 requirements-build.txt（PyInstaller 6.22.3），无需用户手动创建 venv。开发者配置成功后 source .venv/bin/activate 再运行工程检查。项目源码不携带 Windows .venv。

官方依据：https://pyinstaller.org/en/stable/operating-mode.html；https://docs.astral.sh/uv/reference/installer/；https://support.apple.com/en-us/102445 。
