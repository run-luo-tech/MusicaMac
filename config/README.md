# 配置与持久化

默认 schema_version=1、volume=0.65、selection=random、version=0.3.1。运行入口在当前用户 Application Support/MusicaMac/config/app.json 创建配置；正式活动保存生效版本快照。已有 v0.2.0 配置保留，生效版本从程序读取；升级不覆盖个人音量配置。包内 config/app.json 只是默认值说明，不要求修改签名应用内容。

data 内 SQLite 与编号 MP3 保存歌曲、活动和使用记录；更新 .app 保留此目录。备份和迁移前退出软件。活动未结束时禁止曲库编辑，避免改变去重身份。
