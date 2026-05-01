# 使用指南

## 一次性设置（Claude Projects）

1. 在 Claude app 创建 Project，命名 **Vocal Coach**。
2. 打开 Project → **Instructions**，把 `coach-prompt.md` 全文粘贴进去保存。
3. 打开 Project → **Knowledge**（右上角 + Add files），上传 `training-journal.md`。
4. 完成。以后所有声乐对话都在这个 Project 里开新 chat。

## 第一次对话（摸底）

1. 在 Project 里 New chat。
2. 直接打个招呼即可，比如"开始摸底"。教练会主动发 5 段录音任务。
3. 按要求录音（一次发齐或分多次都可以，每段录完直接拖进对话）：
   1. 唇颤滑音（上下行）
   2. 持续元音 /ɑ/ 8 秒
   3. /i e a o u/ 序列
   4. 大调音阶
   5. 自由片段 30 秒（最重要，决定"目标音色"）
4. 5 段收齐后，教练会输出 `=== TRAINING JOURNAL (FULL REPLACE) ===` 整块。
5. **更新日志文件**：
   - 复制整块（不含围栏标记）。
   - 在本地编辑器里把 `training-journal.md` 内容整体替换。
   - 回到 Project Knowledge → 删除旧的 `training-journal.md` → 上传新版本。

## 日常练习对话（摸底之后）

1. 在 Project 里 New chat，标题写 `Day 5` 之类。
2. 一句话开场，比如：「Day 5，今天练了 Week 1 的 SOVT 长音」+ 拖入当日录音（1–3 段都行）。
3. 教练给反馈，末尾输出 `=== TRAINING JOURNAL UPDATE (APPEND/PATCH) ===` 块。
4. **更新日志**：
   - **Day N 日志条目** → 粘贴到日志「每日日志」区顶部
   - **复发问题清单更新** → 整体替换「复发问题清单」节
   - **current_day / last_session_date** → 更新到顶部 frontmatter
   - 重新上传到 Project Knowledge

## 周回顾

每周末（Day 7、14、21、28）开一个新 chat，发：「我们做一次周回顾」+ 可选地附带本周一段代表性录音。教练会综合本周日志、调整下周计划、输出更新后的 30 天 plan 块。

## 录音规范

- 安静环境，麦克风距嘴**一拳**左右
- **不要**加伴奏、混响、修音、自动调音
- 文件格式：WAV / MP3 / m4a / 微信语音都行
- 单段时长：摸底任务按要求；日常练习每段 15–60 秒最佳，太长不易聚焦
- 重录原则：教练说听不清就重录，不要硬猜

## 沟通技巧

- 卡壳时直接说**身体感受**：「唱到 G4 喉咙就紧」「换声区那里像被掐住」比硬唱更有用
- 情绪化时直说：「这周我很泄气」教练会拉回客观可改进点，不会空洞安慰
- 不确定术语时直接问：「什么是 appoggio」教练会用白话解释

## 日志维护

- 每周末让教练做一次**压缩**：旧日常条目可以归档，只保留每周关键发现，避免日志膨胀超出 Project Knowledge 上下文
- 每月末（Day 30）让教练做**总评**：30 天前后对比、下一阶段方向（建议下一阶段开新 Project，归档老日志）

## 出问题时

- 教练忘了自己是教练 / 跑题 → 在新 chat 里重开，确认 Project Instructions 仍然是 `coach-prompt.md`
- 教练胡乱编数字 → 直接说"不要编 cent 数字，只给听感"，提醒它遵守 prompt 中的"诚实优先"准则
- 日志越来越乱 → 让教练输出一个"压缩版" full replace
