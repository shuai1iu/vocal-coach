# 使用指南 — 健身教练

## 两条启动路径

### 路径 1：全新开始（无 Gemini 历史）

1. Claude app 创建 Project，命名 **Fitness Coach**
2. **Instructions**：粘贴 `coach-prompt.md` 全文
3. **Files**：上传 `training-journal.md`（默认 `status: intake_pending`）
4. New chat → 打个招呼 → 教练自动进入**摸底模式**，分组询问基本数据/目标/训练史/伤病/装备/营养睡眠
5. 摸底完成 → 教练输出 FULL REPLACE 块 → 你替换 journal 重新上传

### 路径 2：从 Gemini 历史接续 ⭐

1. **导出 Gemini 数据**：takeout.google.com → "My Activity" → 内容类型选 **Bard / Gemini** → JSON 格式 → 下载 zip
2. **蒸馏成档案**：
   ```sh
   cd fitness-coach/distiller
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
   python distill.py path/to/your-gemini-export.zip -o ../training-journal.md
   ```
3. 蒸馏完成会得到一份已填好的 `training-journal.md`，含 `status: active` + `last_session_state`
4. Claude app 创建 Project **Fitness Coach** → Instructions 粘贴 `coach-prompt.md` → Files 上传蒸馏后的 journal
5. New chat → 打个招呼 → 教练自动进入**接续模式**，引用你上次和 Gemini 聊到的话题 + 核对当前伤病/体重
6. 之后流程与路径 1 一致

## 日常对话流程（摸底/接续完成之后）

1. New chat，标题写 `Week 2 Day 3` 之类
2. 一句话开场 + 当日训练数据：
   ```
   Week 2 Day 3，今天上肢推日：
   卧推 60kg×8 / 8 / 6 RPE 8.5
   军推 35kg×10 / 8 / 8 RPE 8
   绳索下压 ...
   主观能量 7/10，左肩没事
   ```
3. 教练给反馈，末尾输出 PATCH 块
4. 复制 **当日日志条目** → 粘到 journal 「每日日志」顶部
5. 复制 **复发清单更新** → 整体替换原清单
6. 更新顶部 `last_session_date` / `current_week`
7. 重新上传 journal 到 Project Files

## 周回顾

每周末开新 chat：「我们做一次周回顾」+ 可选附本周关键视频。教练综合本周日志，更新下周 plan 块。

## 数据规范

- **训练记录**：动作 × 组 × 次 × 重量 × RPE
- **视频**：主项动作建议每 2 周录一次（深蹲、硬拉、卧推、引体），手机横屏，距 2-3 米侧前方
- **营养**：不需要详细 macros，给个粗描述就行（"早午餐都按 1 拳蛋白 + 2 拳碳水"）
- **睡眠**：时长 + 主观质量（差/中/好）

## 沟通技巧

- 不舒服直接说："今天小腿提脚跟时膝盖外侧有点紧" 比硬练有用
- 情绪化时直说："这周没动力训练" 教练会拉回到客观可改进点（睡眠？过度训练？）
- 不确定术语时直接问：「什么是 Pin Squat」教练会用白话解释

## 安全准则

- ⭐ **任何 red flag**（夜痛、放射痛、神经症状）→ 教练会建议先就医，**不要**绕开这条
- 教练不是医生，不做诊断，复杂膳食疾病/术后康复请咨询专业人士
- 接续模式下，教练会主动核对伤病状态——这是**安全机制**，请认真回答

## 日志维护

- 每周末让教练做一次**压缩**：旧日常条目可以归档，只保留每周关键发现
- 4 周 mesocycle 末做**周期总评**：评估目标达成、调整下个周期方向

## 出问题时

- 教练忘了自己是教练 / 跑题 → 在新 chat 里重开，确认 Project Instructions
- 教练给出与已知伤病冲突的建议 → 立即指出"我有 X 伤"，教练应当道歉并改方案
- 蒸馏的 journal 信息有误 → 在对话里直接更正，教练会更新 last_session_state
