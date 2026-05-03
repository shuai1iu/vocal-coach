# History → Zen Master 档案 Distiller

把过往的反思 / 自检 / 哲学讨论 / 禅修类对话蒸馏成结构化档案，作为新 Project 的初始记忆。

## 输入支持

- Google Takeout 导出的 zip
- `MyActivity.json` / `MyActivity.html`
- 你自己整理的 markdown / 纯文本（推荐——禅类讨论你大概率自己整理过笔记）

如果是 Google Takeout：takeout.google.com → My Activity → Bard/Gemini → JSON。

如果是手动整理的 md：保持时间顺序、用 `## 用户` / `## AI` 之类的小标题区分发言即可。

## 安装

```sh
cd zen-coach/distiller
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
```

## 运行

```sh
# 你整理的 md 文件
python distill.py path/to/your-history.md -o ../training-journal.md

# Takeout zip
python distill.py path/to/takeout-20260601.zip -o ../training-journal.md

# 调试：只看脚本提取出来的 transcript，不调 API
python distill.py path/to/file.md --show-transcript 2>&1 | less
```

## 这个 distiller 的特殊设计

跟其它教练的 distiller 相比，禅师 distiller：

1. **更重视反复主题提炼**：禅师工作的核心就是反复出现的内在模式，schema 把这块放在最优先位置
2. **language_level 自动推断**：从你已经使用的术语推断起步级别，宁低勿高
3. **危机信号红旗**：如果历史里出现过自杀意念/自伤/严重抑郁，强制在档案最显眼位置标注，**不会自作主张抹掉**
4. **矛盾显式列出**：禅类讨论里的前后矛盾很有诊断价值（"自述 X 但行动 Y"），蒸馏器主动找

## 成本

蒸馏 1-3 月、几百条对话的输入 ≈ $1-3。

## 隐私

`.env` / `*.distilled.md` / `gemini-history.*` / 任何你的原始历史文件，都已 gitignore。蒸馏出的 journal 含个人深层信息（情绪 / 困惑 / 关系 / 自我认知），**强烈建议本地存储**，不要上传公开仓库。
