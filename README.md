# MusicaMac · 听歌猜曲

独立 macOS 项目，功能与 Windows v0.2.0 对齐。只导入 MP3，通过文件名提取歌手/歌名；电脑揭晓前只显示编号，主持人手机查离线答案表。不同项目之间没有运行时路径依赖。

## 主持人使用

推荐拿到与电脑架构匹配的 Musica.app，复制到“应用程序”后双击；不安装 Python、pip、Homebrew、Xcode。当前 Windows 主机无法构建或验证原生 .app；本目录暂未包含可直接运行的 Mac 原生二进制。

暂时没有 .app 时，可解压 MusicaMac-Source-v0.2.0.zip，双击“首次配置并启动.command”。脚本首次联网下载 uv、私有 Python 3.12 与依赖，均在项目 .runtime/.venv，不需要 sudo、不更改 shell 配置。配置成功后再次使用不需要联网。若 command 文件没有执行权限，在终端进入目录运行 bash ./首次配置并启动.command。

## 给其他主持人制作免环境应用

在 Mac 上双击“生成Mac应用.command”。它配置私有环境、安装固定依赖、运行测试、生成 .app、启动检查、导出原生 ZIP。Apple Silicon 与 Intel 分别构建。产物位于 releases/MusicaMac-架构-v0.2.0。不要求主持人重复这个构建步骤；由维护者完成一次后分发 .app 即可。

GitHub Actions 手动构建模板在 .github/workflows/build-macos.yml，使用 macos-14 (arm64) 和 macos-15-intel。未上传或运行远程任务，尚不能视为成功产物。最终最低 macOS 版本需以实际构建依赖、系统和实机测试为准，当前 CI 验收目标分别为 macOS 14/15。

数据：~/Library/Application Support/MusicaMac/data。退出后备份整个 data；更新应用不覆盖此目录。Mac 首次运行使用空曲库。迁移 Windows 曲库时整体复制 data，保留数据库及 audio，切勿在软件打开时覆盖。

界面使用 PingFang SC 与 Menlo；Cmd+Q 退出。首次未公证应用可能被 macOS 拦截，按 Apple 的“系统设置 → 隐私与安全性 → 仍要打开”对单个可信应用处理；不关闭系统安全防护。当前构建脚本采用 PyInstaller 临时签名，正式广泛分发还需要 Developer ID 签名与公证。

说明书：docs/manual/Musica-使用说明书.pdf；TeX 和独立截图在同目录。软件使用与活动操作见说明书。
