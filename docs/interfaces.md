# 接口与状态

- core.models：Song 不可变；parse_filename 优先按两侧有空白的横线拆分，否则按首个横线拆分，兼容 ASCII、全角、长短横线等常见字符；两侧空白自动去除，无法解析返回空歌手；group_key 折叠空白、忽略大小写；choose_song 输入歌曲与已用组，返回候选或 ValueError。
- adapters.store.Store：单 UI 线程 SQLite 连接，事务保存活动和出题；record_play 幂等，返回题序；无打开轮次拒绝记录。
- adapters.library.Library：验证真实 MP3 和时长、原文件摘要、复制和去 ID3；失败回滚数据库并清理新副本；返回编号或重复原因。HTML 文本转义、无外部网络资源。
- adapters.audio.Audio：延迟初始化 pygame；play/busy 确认播放、pause/resume/stop/volume，不发布系统媒体元数据。
- pipelines.game.Game：当前候选/揭晓属内存，活动/已用属 Store；next/previous 清除揭晓；played 由播放启动成功后调用。
- apps.desktop：Tk 事件循环每 250ms 更新播放状态。正式禁用管理与按编号选题，错误转换成不含原始路径的提示。

单位：时长秒，播放位置毫秒，时间 UTC ISO8601；编号至少六位，无人为上限。单实例命名互斥锁避免同时修改同一曲库。

macOS 入口负责 Application Support 用户目录与 fcntl 进程锁，运行配置自动创建；无 Windows mutex 依赖。
