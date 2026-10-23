与 Windows v0.3.0 同步，新增可调整的播放进度，并提供 Mac 原生安装升级包。

## 选择下载

- **Apple Silicon（M 系列）**：MusicaMac-arm64-v0.3.0.dmg。
- **Intel Mac**：MusicaMac-x86_64-v0.3.0.dmg。
- 对应架构也提供 ZIP；普通用户无需下载 Source code，无需安装 Python。

## 首次安装与从 v0.2.0 升级

1. 退出已运行的 Musica，备份 `~/Library/Application Support/MusicaMac/data`。
2. 打开对应架构 DMG，将 Musica.app 拖到 Applications；已有旧版时选择“替换”。如果以前安装在其他位置，替换那里的同名 app。
3. 从“应用程序”打开 v0.3.0，原歌曲、编号、活动记录和配置继续保留，可以恢复未完成活动。

新用户和旧用户使用同一个发行包，数据始终位于应用外的 Application Support。包使用临时签名、尚未公证；首次被 macOS 拦截时，确认来源后在“系统设置 → 隐私与安全性 → 仍要打开”处理该应用。

## 新功能

- 点击或拖动进度条松开后定位，播放中继续、暂停中保持暂停。
- 播放前可预选起点，实际成功播放才记题，反复定位不重复计题、不揭晓答案。
- 方向键调整 5 秒，Home 回开头、End 到末尾附近；重播从头开始，切题清除旧位置。

## 验证

29 项回归覆盖进度、曲库、活动、Mac 数据位置与旧配置保留。两个架构分别在 GitHub Mac runner 构建，验证包内 Tk/MP3/定位、旧歌曲/活动/配置保留、架构与签名、DMG 完整性；实际结果见本版本关联的 Actions 运行及各架构 build-verification.json。

CI 验收系统为 macOS 14（arm64）和 macOS 15（Intel）。v0.2.0 已由用户确认在 Mac 可用；新版自动化验证不代替目标电脑的真实声音试听。MP3 定位精度随编码而异。发行包不含用户歌曲、数据库或答案表。

**English:** Adds click/drag seeking, paused seeking and start-position selection. Download the DMG for Apple Silicon (arm64) or Intel (x86_64), quit the old app and replace Musica.app in Applications. Libraries, permanent IDs, sessions and settings remain in Application Support. Native ZIPs are also available; Python is not required. Builds use ad-hoc signatures and are not Developer ID notarized.
