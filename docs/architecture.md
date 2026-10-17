# 架构

apps → pipelines → core/adapters；core 处理身份、分组和选题；adapters 封装 MP3、SQLite、导出和音频；pipelines 管测试/活动/轮次，apps 控制可见内容。数据库格式与 Windows 兼容，通用模块独立复制固定版本，不依赖 Windows 项目位置。

入口 run.py 负责用户目录、配置和 macOS fcntl 进程锁。数据写入 ~/Library/Application Support/MusicaMac，不写 .app 内容。锁文件由进程持有，退出释放。正式游戏生命周期沿用 Windows；中途退出可恢复，测试不记题。

依赖归属：源码首次配置脚本下载项目私有 uv/Python/依赖；维护者 build_macos.py 在本机架构构建自包含 .app；最终主持人无需开发环境。Windows 不伪造 Mac 二进制。失败返回真实非零状态，不输出假成功应用包。

验收目标：原生 arm64/x86_64 各自打包；真实 Tk/声卡与 .app 启动；数据目录不随 app 替换丢失；普通账号无需 sudo。通用逻辑本机验证，macOS 行为未实测。
