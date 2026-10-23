# 验证与限制

2026-10-17：21 项通用及 UI/路径回归在 Windows Python 3.14 环境通过；使用显式 VIRTUAL_ENV 指向测试解释器，独立工作目录为 MusicaMac。所有测试用临时曲库，未读写用户歌曲。shell 脚本用 bash -n 语法检查通过。构建入口在非 macOS 直接拒绝，避免输出虚假应用包。

待 Mac 执行：uv 首次下载、Python 3.12/Tk 环境、MP3 真声卡、fcntl 单实例、PingFang 字体、Cmd+Q、打包 .app 启动、不同最低系统版本、签名与 Gatekeeper。构建脚本及 CI 将运行测试和原生产物启动检查；本次未执行远端任务，未提供伪造的 .app。

checks 使用 python scripts/verify.py，优先选择激活环境 VIRTUAL_ENV 或本地 .venv。Windows 本机验证借用现有解释器仅为测试工具，不构成 Mac 项目运行依赖。

## v0.3.0（2026-10-23）

用户已确认 v0.2.0 可在 Mac 使用；上面的“未实测”描述属于 2026-10-17 历史状态。新增定位功能同步自 Windows aab5210，保留 Mac 字体、入口、进程锁与用户目录。

本机 Windows 使用隔离数据运行 29 项通用及 UI/路径回归通过，包含真实静音 MP3 绝对定位、暂停定位、拖动预览、计题幂等、切题重置和 v0.2.0 配置保留。原生构建分别在 GitHub macos-14 arm64/macOS 15 Intel 执行；实际原生结果见对应 workflow 运行及随产物输出的 build-verification.json，不能用本机通用测试替代。

原生验收运行实际 .app 内的 Tk 与 MP3 堆栈，在隔离 HOME 的旧 schema/config/活动上测试起点预选、实际播放、定位、暂停定位、答案隐藏，再比较数据库逻辑内容与配置/音频摘要；检查 Mach-O 架构、bundle identifier/版本、临时签名和 DMG 校验。数据格式与位置不变，替换 app 不改写用户数据。真实声卡听感与首次 Gatekeeper 交互由目标电脑使用验证，未用静音 CI 冒充。
