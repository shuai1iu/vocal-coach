# Vocal Coach — 自动化压测 Harness

对 `coach-prompt.md` 的行为做自动化校验。**不测听感准确度**（那需要标注真人录音），只测教练的逻辑骨架是否符合 prompt 设计。

## 测试覆盖

10 个用例，3 个类别：

| 类别 | 测试什么 |
|---|---|
| **behavioral** | 模式切换 (intake/active)、格式合规、抗跑题、无音频不诊断 |
| **judgment** | 抗谄媚、拒绝编造数字、复发问题主动追踪、可执行性、术语白话解释 |
| **format** | 必输出 JOURNAL UPDATE 块 |

具体见 `cases.py`。

## 运行

```bash
cd tests
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# .env 已被 gitignore，需要先在 tests/.env 写入：
# ANTHROPIC_API_KEY=sk-...

python run_tests.py
```

只跑某几个用例：

```bash
python run_tests.py T01_intake_trigger T04_anti_sycophancy
```

## 输出

- `tests/reports/report-<timestamp>.md` — 当次详细报告
- `tests/reports/latest.md` — 最新报告软引用

每个用例会展示：
- 通过/失败 + 每个 assertion 状态
- 完整对话 transcript（折叠）
- LLM-as-judge 的判断理由

## 模型

- 教练：`claude-opus-4-7`（与 Claude app 同档）
- 评判：`claude-sonnet-4-6`

## 成本估算

全套 10 个用例 ≈ 15-20 次 API 调用（部分用例多轮 + judge），启用 prompt caching 后单次成本 < $0.05。整套 < $0.5。

## 局限

- **同模型评判同模型**：判断维度由 Claude 评 Claude，不是独立 ground truth。能抓 prompt 设计漏洞，不能验证听感。
- **没有真实音频**：要测准确听感需要 labeled vocal samples（用户录的或公开数据集）。
- **判官有方差**：LLM-as-judge 同一输入可能给出略不同结论。Rubric 写得越严越稳定。

## 添加新用例

在 `cases.py` 里追加 dict。assertion 类型见文件顶部 docstring。
