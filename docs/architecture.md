# 架构

apps → pipelines → core/adapters；core 处理身份、分组和选题；adapters 封装 MP3、SQLite、导出和音频；pipelines 管测试/活动/轮次，apps 控制可见内容。数据库格式与 Windows 兼容，通用模块独立复制固定版本，不依赖 Windows 项目位置。

入口 run.py 负责用户目录、配置和 macOS fcntl 进程锁。数据写入 ~/Library/Application Support/MusicaMac，不写 .app 内容。锁文件由进程持有，退出释放。正式游戏生命周期沿用 Windows；中途退出可恢复，测试不记题。

依赖归属：源码首次配置脚本下载项目私有 uv/Python/依赖；维护者 build_macos.py 在本机架构构建自包含 .app；最终主持人无需开发环境。Windows 不伪造 Mac 二进制。失败返回真实非零状态，不输出假成功应用包。

v0.3.0 同步 Windows aab5210 的进度控制，保留本项目原生字体与快捷键。定位状态属 Audio，拖动预览与未播放起点属 Desktop，不改变 Game/Store 的记题规则或数据格式。

发行按 arm64/x86_64 分别构建，稳定 bundle identifier 为 org.musica.mac。DMG 包含 Musica.app 与 Applications 链接，首次复制安装、更新替换同名 app；数据/配置留在 Application Support。包内测试在隔离 HOME 上检查真实 Tk/MP3/定位和旧活动保留，DMG 经 hdiutil verify。用户确认 v0.2.0 可在 Mac 使用；v0.3.0 原生验证以本次 CI 记录为准。
