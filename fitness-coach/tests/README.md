# Fitness Coach — 自动化压测 Harness

12 个用例，对应 `coach-prompt.md` 的关键行为属性。

| 类别 | 测什么 |
|---|---|
| **behavioral** | 模式切换 (intake / continuation / daily)、抗跑题、无数据不开计划 |
| **safety** ⭐ | 已知伤病禁忌不被触发、接续模式必须主动核对伤病状态 |
| **judgment** | 抗谄媚、接续上次话题、可执行性、术语解释、历史推断透明 |
| **format** | JOURNAL UPDATE 块合规 |

特别说明 **safety** 类别——这是健身领域比声乐严重得多的风险点，任一项 FAIL 都意味着 prompt 有真实安全漏洞。

## 运行

```sh
cd fitness-coach/tests
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env

python run_tests.py
# 或只跑某几个：
python run_tests.py T02_continuation_trigger T04_injury_safety_known_contraindication
```

## 测试用例

| ID | 标题 |
|---|---|
| T01_intake_trigger | 摸底模式触发 |
| T02_continuation_trigger | ⭐ 接续模式触发（不重新摸底） |
| T03_continuation_picks_up_thread | 接续模式接上 pending question |
| T04_injury_safety_known_contraindication | ⭐ 已知禁忌时拒绝触发动作 |
| T05_injury_proactive_check_in_continuation | ⭐ 接续模式主动核对伤病状态 |
| T06_anti_sycophancy | 用户错误观念时是否反对 |
| T07_no_data_no_specific_plan | 无数据时不给精确重量 |
| T08_stays_on_topic | 抗跑题 |
| T09_format_compliance | JOURNAL UPDATE 块 |
| T10_actionability | 修正建议具体到动作/重量/RPE |
| T11_term_explanation | 术语带白话锚点 |
| T12_historical_inference_transparent | 历史推断必须明确标注 |

## fixtures

- `intake_pending.md` — 空白摸底状态
- `active_with_continuation.md` — ⭐ 模拟蒸馏后的档案，含 `last_session_state` 和未确认的伤病/体重
- `active_with_injury.md` — 当前有医嘱标明的训练禁忌（轻度椎间盘膨出）

## 输出

- `tests/reports/report-<ts>.md` — 当次详细
- `tests/reports/latest.md` — 最新

## 模型 / 成本

- Coach: `claude-opus-4-7`（与 Claude app 同档）
- Judge: `claude-sonnet-4-6`
- 全套 ~12 次主调用 + ~8 次 judge ≈ $0.5
