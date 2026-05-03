# Zen Master — Claude Project 教练

第三个 Claude Project 教练（前两个：声乐、健身）。这一个最危险也最有意思——禅师不是技能教练，而是一面镜子。

## 这个教练在干什么

- **三模式**：摸底 / 接续 / 日常，由 journal frontmatter 里的 `status` 字段切换
- **渐进语言（L1-L4）**：从世俗语言起步，主动正确使用某术语 ≥3 次后禅师才建议升级
- **自动风格切换**：默认 Soto（温和镜映），检测到合理化 / spiritual bypass / 求肯定时切 Rinzai 直击
- **硬安全边界**：碰到自杀意念 / 自伤 / 急性失控直接停止对话并转介心理热线
- **对话蒸馏**：把过去和别的 LLM（Gemini / ChatGPT）聊过的反思 / 哲学讨论蒸馏成结构化 journal，在新 Project 里"接续"对话

## 文件

```
.
├── coach-prompt.md          # Claude Project Instructions
├── training-journal.md      # Project Files 里的初始模板
├── usage-guide.md           # 使用说明（含安全边界、语言级别、风格切换）
├── distiller/               # 历史聊天蒸馏脚本
│   ├── distill.py
│   ├── prompt.md
│   ├── requirements.txt
│   └── README.md
└── tests/                   # 自动化压测 harness
    ├── run_tests.py
    ├── cases.py
    ├── fixtures/
    ├── requirements.txt
    └── README.md
```

## 快速开始

读 `usage-guide.md`。两条启动路径：

1. **全新开始**：Project 创建 → 粘贴 prompt → 上传空 journal → 摸底
2. **从历史接续**（核心卖点）：跑 `distiller/distill.py` 蒸馏过往对话 → 上传蒸馏 journal → 禅师接续上次的话题

## 自动化压测

12 用例覆盖 safety / style / language / format。详见 `tests/README.md`。

## 设计要点

- **不是治疗师**：硬边界在 `coach-prompt.md` 第 0 节，测试用例 T03 验证
- **不卖弄禅味**：拒绝廉价公案、拒绝开悟时间表、不恭喜"突破"
- **不上术语爬虫**：L1 阶段不抛 L3 术语；引入新术语必带 L1 解释
- **Rinzai 是例外，不是基线**：歧义时默认 Soto；只有自欺信号占消息主体时才切 Rinzai

## 隐私

蒸馏出的 journal 含**深层个人信息**（情绪 / 困惑 / 关系 / 自我认知 / 红旗信号）。
**强烈建议本地存储，不要上传公开仓库**。
`.gitignore` 已排除 `*.distilled.md` / `gemini-history.*` / `.env` / `reports/`。
