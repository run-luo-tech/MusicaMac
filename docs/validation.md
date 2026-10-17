# 验证与限制

2026-10-17：21 项通用及 UI/路径回归在 Windows Python 3.14 环境通过；使用显式 VIRTUAL_ENV 指向测试解释器，独立工作目录为 MusicaMac。所有测试用临时曲库，未读写用户歌曲。shell 脚本用 bash -n 语法检查通过。构建入口在非 macOS 直接拒绝，避免输出虚假应用包。

待 Mac 执行：uv 首次下载、Python 3.12/Tk 环境、MP3 真声卡、fcntl 单实例、PingFang 字体、Cmd+Q、打包 .app 启动、不同最低系统版本、签名与 Gatekeeper。构建脚本及 CI 将运行测试和原生产物启动检查；本次未执行远端任务，未提供伪造的 .app。

checks 使用 python scripts/verify.py，优先选择激活环境 VIRTUAL_ENV 或本地 .venv。Windows 本机验证借用现有解释器仅为测试工具，不构成 Mac 项目运行依赖。
