# v0.3.0 实施与发行

同步 Windows aab5210 的 Audio 绝对定位与 Desktop 拖动/预选逻辑，保留 Mac 的 PingFang SC、Menlo、Cmd+Q、fcntl 锁和 Application Support 数据路径。通用模块固定复制，运行时不引用 Windows 项目。

Audio 接收秒、position 返回毫秒，包含起播偏移；播放中定位继续，暂停中定位保持暂停；未播放时预选位置不记题，实际播放成功才调用 Game.played。重播和切题重置，定位不揭晓答案。

macOS 安装升级采用同名 Musica.app 替换，数据继续在 ~/Library/Application Support/MusicaMac/data，配置在同级 config。新装与升级使用相同原生发行包。分别在 GitHub macos-14 arm64、macos-15-intel x86_64 runner 构建 DMG 和 ZIP；DMG 提供 Applications 链接。保持 bundle identifier org.musica.mac，写入 0.3.0 的 Finder 版本信息，检查原生架构和临时签名。

验收：通用及 UI 回归；v0.2.0 配置保留；Mac 原生构建和包内启动；旧曲库、配置与未完成活动保留；DMG 校验；ZIP 内容检查。v0.2.0 可在 Mac 使用由用户于 2026-10-23 确认，不冒充 v0.3.0 的实机使用验收。新版以实际 CI 结果发布。
