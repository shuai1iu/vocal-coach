# Gemini → Fitness Journal Distiller

把 Google Gemini 的聊天历史蒸馏成结构化健身档案，作为新 Project 的初始记忆。

## 安装

```sh
cd fitness-coach/distiller
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
```

## 导出 Gemini 数据

1. 打开 https://takeout.google.com
2. **Deselect all**
3. 找到 **My Activity**，勾上
4. 点 "All activity data included" → 取消其它，**只勾 Bard / Gemini**
5. 选 JSON 格式（HTML 也行，但 JSON 更稳定）
6. 创建导出 → 等邮件 → 下载 zip

## 运行

```sh
# 直接传 Takeout zip（推荐）
python distill.py path/to/takeout-20260101.zip -o ../training-journal.md

# 或者从已解压的 JSON
python distill.py path/to/MyActivity.json -o ../training-journal.md

# 或者 HTML（解析能力较弱）
python distill.py path/to/MyActivity.html -o ../training-journal.md

# 或者一段你手动整理的文本
python distill.py path/to/manual-transcript.txt -o ../training-journal.md
```

## 调试

```sh
# 查看脚本解析出来的对话流，不调 API
python distill.py path/to/takeout.zip --show-transcript 2>&1 | less
```

## 成本估算

- 启用 prompt caching（蒸馏 prompt 部分缓存）
- 大致：每 100K 输入 token ≈ $0.5；蒸馏一年的 Gemini 闲聊 ≈ $1-3
- 输出本身不大（几 KB markdown），主要成本在输入

## 输出

一份 markdown 档案，schema 见 `prompt.md`。关键字段：

- `status: active` + `distilled_from_gemini: true` → 让 coach prompt 进入接续模式
- `last_session_state` → 教练第一句话的引用素材
- `# 矛盾与待澄清` → 教练在第一次会话主动核对
- `# 伤病与禁忌` → ⭐ 安全关卡

## 把档案投入使用

1. 把蒸馏出的 `training-journal.md` 上传到 Claude Project 的 Files
2. Project Instructions 是 `coach-prompt.md`
3. 新建 chat → 教练自动识别 `status: active` + `last_session_state` → 进入接续模式

## 限制

- **隐私**：聊天记录会发给 Anthropic API。如果 Gemini 历史里含敏感个人信息（医疗、财务），评估后再决定是否蒸馏。
- **失真**：LLM 蒸馏不是无损压缩。重要的具体数字（体重、1RM）可能被概括掉。蒸馏完务必通读一遍档案。
- **时效**：如果 Gemini 历史最后一条对话距今 >3 个月，教练在接续模式会主动要求核对——这是设计内的，不是 bug。

## 安全提醒

- `.env` 已被 `.gitignore` 排除
- 蒸馏出的 journal 也建议本地存储，不直接 commit 进公开仓库（可能含个人健康信息）
