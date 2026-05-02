"""
Fitness Coach prompt — automated behavioral test harness.

Usage:
    cd fitness-coach/tests
    pip install -r requirements.txt
    python run_tests.py [optional_case_ids...]
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from cases import CASES

TESTS_DIR = Path(__file__).resolve().parent
COACH_DIR = TESTS_DIR.parent
FIXTURES = TESTS_DIR / "fixtures"
REPORTS = TESTS_DIR / "reports"
REPORTS.mkdir(exist_ok=True)

# Load .env from tests/.env, with fallback to repo-root tests/.env
load_dotenv(TESTS_DIR / ".env")
if not os.getenv("ANTHROPIC_API_KEY"):
    load_dotenv(COACH_DIR.parent / "tests" / ".env")  # share key with vocal-coach

COACH_PROMPT = (COACH_DIR / "coach-prompt.md").read_text(encoding="utf-8")

MODEL = "claude-opus-4-7"
JUDGE_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096

# Pace between cases (seconds) to respect Tier 1 rate limit (30K input tokens/min on Opus)
SLEEP_BETWEEN_CASES = int(os.getenv("SLEEP_BETWEEN_CASES", "35"))

client = anthropic.Anthropic(max_retries=5)  # SDK retries 429 with backoff


def text_of(message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def coach_call(messages: list[dict]) -> tuple[str, dict]:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": COACH_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages,
    )
    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", 0),
        "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0),
    }
    return text_of(resp), usage


def judge_call(rubric: str, conversation: list[dict], target_idx: int) -> dict:
    transcript = []
    for i, m in enumerate(conversation):
        marker = " ← evaluating this" if i == target_idx else ""
        transcript.append(f"[{m['role']}{marker}]\n{m['content']}")
    transcript_text = "\n\n".join(transcript)

    judge_prompt = f"""You are a strict, terse test evaluator for a fitness-coach prompt's behavior.

Rubric (criterion for PASS):
{rubric}

Conversation transcript:
---
{transcript_text}
---

Apply the rubric to the marked assistant message. Be strict — when the rubric says "if X, FAIL", FAIL it.

Output format (exactly):
Line 1: PASS or FAIL
Line 2-3: One-sentence reason (Chinese OK)."""

    resp = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": judge_prompt}],
    )
    out = text_of(resp).strip()
    first_line = out.split("\n", 1)[0].strip().upper()
    passed = first_line.startswith("PASS")
    return {"passed": passed, "reason": out}


@dataclass
class AssertionResult:
    type: str
    passed: bool
    detail: str
    rationale: str = ""


def run_assertion(assertion: dict, conversation: list[dict]) -> AssertionResult:
    atype = assertion["type"]
    rationale = assertion.get("rationale", "")
    target_idx = assertion.get("in_response", -1)

    assistant_msgs = [(i, m) for i, m in enumerate(conversation) if m["role"] == "assistant"]
    if target_idx == -1:
        target_i, target_msg = assistant_msgs[-1]
    else:
        target_i, target_msg = assistant_msgs[target_idx]
    target_text = target_msg["content"]

    if atype == "contains":
        text = assertion["text"]
        ok = text in target_text
        return AssertionResult(atype, ok, f"contains '{text}': {ok}", rationale)
    if atype == "not_contains":
        text = assertion["text"]
        ok = text not in target_text
        return AssertionResult(atype, ok, f"not_contains '{text}': {ok}", rationale)
    if atype == "regex":
        pat = assertion["pattern"]
        ok = bool(re.search(pat, target_text))
        return AssertionResult(atype, ok, f"regex '{pat}': {ok}", rationale)
    if atype == "all_of_contains":
        items = assertion["items"]
        missing = [s for s in items if s not in target_text]
        ok = not missing
        return AssertionResult(atype, ok, f"missing: {missing}" if missing else "all present", rationale)
    if atype == "any_of_contains":
        items = assertion["items"]
        present = [s for s in items if s in target_text]
        ok = bool(present)
        return AssertionResult(atype, ok, f"matched: {present}" if present else "none of " + str(items), rationale)
    if atype == "judge":
        result = judge_call(assertion["rubric"], conversation, target_i)
        return AssertionResult(atype, result["passed"], result["reason"], rationale)

    return AssertionResult(atype, False, f"unknown assertion type: {atype}", rationale)


@dataclass
class CaseResult:
    id: str
    title: str
    category: str
    passed: bool
    assertions: list[AssertionResult]
    conversation: list[dict]
    usage: list[dict] = field(default_factory=list)
    error: str | None = None
    duration_s: float = 0.0


def run_case(case: dict) -> CaseResult:
    t0 = time.time()
    journal_path = FIXTURES / f"{case['journal']}.md"
    journal = journal_path.read_text(encoding="utf-8")

    conversation: list[dict] = []
    usages: list[dict] = []

    try:
        for turn in case["turns"]:
            content = turn["content"]
            if turn["role"] == "user" and not conversation:
                content = f"<training_journal>\n{journal}\n</training_journal>\n\n{content}"
            conversation.append({"role": "user", "content": content})
            assistant_text, usage = coach_call(conversation)
            conversation.append({"role": "assistant", "content": assistant_text})
            usages.append(usage)

        results = [run_assertion(a, conversation) for a in case["assertions"]]
        passed = all(r.passed for r in results)
        return CaseResult(
            id=case["id"],
            title=case["title"],
            category=case["category"],
            passed=passed,
            assertions=results,
            conversation=conversation,
            usage=usages,
            duration_s=round(time.time() - t0, 1),
        )
    except Exception as e:
        return CaseResult(
            id=case["id"],
            title=case["title"],
            category=case["category"],
            passed=False,
            assertions=[],
            conversation=conversation,
            usage=usages,
            error=f"{type(e).__name__}: {e}",
            duration_s=round(time.time() - t0, 1),
        )


def render_report(results: list[CaseResult]) -> str:
    total = len(results)
    passed = sum(1 for r in results if r.passed)

    total_in = sum(u["input_tokens"] for r in results for u in r.usage)
    total_out = sum(u["output_tokens"] for r in results for u in r.usage)
    cache_read = sum(u["cache_read_input_tokens"] for r in results for u in r.usage)
    cache_write = sum(u["cache_creation_input_tokens"] for r in results for u in r.usage)

    by_cat: dict[str, dict] = {}
    for r in results:
        d = by_cat.setdefault(r.category, {"pass": 0, "fail": 0})
        d["pass" if r.passed else "fail"] += 1

    lines = [
        f"# Fitness Coach Prompt — Test Report",
        "",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Coach model: `{MODEL}`",
        f"- Judge model: `{JUDGE_MODEL}`",
        "",
        f"## Summary",
        "",
        f"**{passed} / {total} passed** ({100 * passed // total if total else 0}%)",
        "",
        "| Category | Pass | Fail |",
        "|---|---:|---:|",
    ]
    for cat, d in sorted(by_cat.items()):
        lines.append(f"| {cat} | {d['pass']} | {d['fail']} |")
    lines += [
        "",
        "## Token usage",
        "",
        f"- Input (uncached): {total_in:,}",
        f"- Output: {total_out:,}",
        f"- Cache read: {cache_read:,}",
        f"- Cache write: {cache_write:,}",
        "",
        "## Per-case results",
        "",
    ]

    for r in results:
        emoji = "PASS" if r.passed else "FAIL"
        lines.append(f"### [{emoji}] `{r.id}` — {r.title}")
        lines.append("")
        lines.append(f"- Category: `{r.category}`  •  Duration: {r.duration_s}s")
        if r.error:
            lines.append(f"- **ERROR:** `{r.error}`")
        lines.append("")
        if r.assertions:
            lines.append("**Assertions:**")
            for a in r.assertions:
                e = "PASS" if a.passed else "FAIL"
                rat = f" — _{a.rationale}_" if a.rationale else ""
                lines.append(f"- [{e}] `{a.type}`{rat}")
                detail = a.detail.replace("\n", " ").strip()
                if len(detail) > 280:
                    detail = detail[:280] + "..."
                lines.append(f"  - {detail}")
            lines.append("")
        lines.append("<details><summary>Conversation transcript</summary>")
        lines.append("")
        for m in r.conversation:
            lines.append(f"**{m['role']}**:")
            lines.append("")
            lines.append("```")
            content = m["content"]
            if len(content) > 2000:
                content = content[:2000] + "\n\n[... truncated ...]"
            lines.append(content)
            lines.append("```")
            lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. Put it in tests/.env", file=sys.stderr)
        sys.exit(1)

    only = set(sys.argv[1:])
    cases = [c for c in CASES if not only or c["id"] in only]
    print(f"Running {len(cases)} cases against {MODEL}...\n")

    results: list[CaseResult] = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']} — {case['title']}")
        r = run_case(case)
        results.append(r)
        status = "PASS" if r.passed else "FAIL"
        print(f"    {status} ({r.duration_s}s)")
        if not r.passed:
            for a in r.assertions:
                if not a.passed:
                    short = a.detail.split("\n")[0][:120]
                    print(f"      x {a.type}: {short}")
        if r.error:
            print(f"    ERROR: {r.error}")
        print()
        if i < len(cases) and SLEEP_BETWEEN_CASES > 0:
            time.sleep(SLEEP_BETWEEN_CASES)

    report = render_report(results)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = REPORTS / f"report-{timestamp}.md"
    report_path.write_text(report, encoding="utf-8")
    latest = REPORTS / "latest.md"
    latest.write_text(report, encoding="utf-8")

    print(f"Report written: {report_path}")
    print(f"  (also: {latest})")

    passed = sum(1 for r in results if r.passed)
    print(f"\nFinal: {passed}/{len(results)} passed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
