本次接入用户提供的 Musica Logo。

- 主界面左上角常驻显示 Logo，Finder/Dock 使用新的应用图标。
- PNG 与 ICNS 均内置在应用包中，无需原图文件或联网。
- 保留 v0.3.0 的进度调整、暂停定位、活动恢复和全部原有功能。

**Apple Silicon（M 系列）**选择 MusicaMac-arm64-v0.3.1.dmg；**Intel Mac**选择 MusicaMac-x86_64-v0.3.1.dmg。也提供对应 ZIP。

安装/升级：先退出旧版并备份 data，打开 DMG，把 Musica.app 拖到 Applications，已有旧版时选择“替换”。歌曲、编号、活动与配置保留在 `~/Library/Application Support/MusicaMac`，不会因替换应用而丢失。

两个架构分别在 Mac runner 运行 29 项回归、包内 Logo/播放/定位检查、旧数据保留、架构/签名及 DMG 校验；本地另核对 ICNS/PNG 与源码资源一致。原生验证结果随附件 build-verification JSON 提供。

采用临时签名，尚未 Developer ID 公证；首次若被系统拦截，确认来源后按“系统设置 → 隐私与安全性 → 仍要打开”处理。真实声音请在活动前试听。Source code 为开发源码，普通用户选择 DMG/ZIP。
