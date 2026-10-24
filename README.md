# MusicaMac · 听歌猜曲

v0.3.1，独立 macOS 项目，与 Windows v0.3.1 对齐，新增主界面 Logo 和 Finder/Dock 应用图标。继续支持点击/拖动播放进度、暂停定位与播放前预选起点。只导入 MP3，通过文件名提取歌手/歌名；电脑揭晓前只显示编号，主持人手机查离线答案表。不同项目之间没有运行时路径依赖。

## 主持人使用

从 [GitHub Releases](https://github.com/run-luo-tech/MusicaMac/releases/latest) 下载对应架构的 **DMG**：Apple Silicon（M 系列芯片）选 arm64，Intel 选 x86_64。打开 DMG，将 Musica.app 拖到 Applications，再从“应用程序”启动；无需 Python、pip、Homebrew 或 Xcode。也提供 ZIP，可解压后复制其中的 Musica.app。

**从 v0.2.0 升级：**先退出旧版并备份数据，再把新版 Musica.app 拖到原安装位置，选择“替换”。新用户和旧用户使用同一个包。歌曲、永久编号、活动记录和设置在应用外保存，替换 .app 不会覆盖它们。v0.2.0 的 Mac 可用性已由用户于 2026-10-23 确认；v0.3.1 原生构建与验证记录见对应 Release。

进度条：点击或拖动松开后定位；播放中继续播放，暂停中保持暂停。播放前可预选起点，实际播放成功才记题。方向键调整 5 秒，Home 回开头、End 到末尾附近；重新播放从头开始，切题清除起点。MP3 定位精度取决于编码。

开发者也可下载对应版本 Source code，解压后双击“首次配置并启动.command”。脚本首次联网下载 uv、私有 Python 3.12 与依赖，均在项目 .runtime/.venv，不需要 sudo、不更改 shell 配置。配置成功后再次使用不需要联网。若 command 文件没有执行权限，在终端进入目录运行 bash ./首次配置并启动.command。

## 给其他主持人制作免环境应用

在 Mac 上双击“生成Mac应用.command”。它配置私有环境、安装固定依赖、运行测试、生成 .app、验证包内启动与音频定位、检查旧数据保留，导出原生 DMG/ZIP。Apple Silicon 与 Intel 分别构建。产物位于 releases/MusicaMac-架构-v0.3.1；build-verification.json 记录实际架构、系统、功能验证及发行文件摘要。普通用户直接下载发行包。

GitHub Actions 手动构建入口在 .github/workflows/build-macos.yml，分别使用 macos-14（arm64）和 macos-15-intel（x86_64）。当前原生验收目标为 macOS 14/15；具体运行记录以 Release 链接的 Actions 结果为准。

数据：~/Library/Application Support/MusicaMac/data。退出后备份整个 data；更新应用不覆盖此目录。Mac 首次运行使用空曲库。迁移 Windows 曲库时整体复制 data，保留数据库及 audio，切勿在软件打开时覆盖。

界面使用 PingFang SC 与 Menlo；Cmd+Q 退出。首次未公证应用可能被 macOS 拦截，按 Apple 的“系统设置 → 隐私与安全性 → 仍要打开”对单个可信应用处理；不关闭系统安全防护。当前构建脚本采用 PyInstaller 临时签名，正式广泛分发还需要 Developer ID 签名与公证。

说明书：docs/manual/Musica-使用说明书.pdf；TeX 和独立截图在同目录。软件使用与活动操作见说明书。
