"""
Distill Google Gemini chat history into a structured fitness journal.

Usage:
    python distill.py path/to/MyActivity.json [-o output.md]
    python distill.py path/to/takeout.zip [-o output.md]
    python distill.py path/to/MyActivity.html [-o output.md]
    python distill.py path/to/raw-text.txt [-o output.md]

Auto-detects format. For Takeout zip files, looks for the Bard/Gemini activity
file inside.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

PROMPT = (ROOT / "prompt.md").read_text(encoding="utf-8")

MODEL = "claude-opus-4-7"
MAX_TOKENS = 8192


# ---------------- input format handling ---------------- #

def find_activity_file_in_zip(zip_path: Path) -> tuple[str, bytes]:
    """Look inside a Takeout zip for the Bard/Gemini activity file.
    Returns (filename, raw_bytes)."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        # Common Takeout paths (any of these may be present)
        candidates = [
            n for n in names
            if any(s in n.lower() for s in ("bard", "gemini"))
            and any(n.lower().endswith(ext) for ext in (".json", ".html"))
            and "myactivity" in n.lower()
        ]
        if not candidates:
            # Fallback: any json/html with bard/gemini in path
            candidates = [
                n for n in names
                if any(s in n.lower() for s in ("bard", "gemini"))
                and any(n.lower().endswith(ext) for ext in (".json", ".html"))
            ]
        if not candidates:
            raise SystemExit(
                f"Could not find Bard/Gemini activity file in {zip_path}.\n"
                f"Files in zip: {names[:20]}{'...' if len(names) > 20 else ''}"
            )
        # Prefer JSON over HTML if both available
        candidates.sort(key=lambda n: 0 if n.endswith(".json") else 1)
        chosen = candidates[0]
        print(f"Using {chosen} from zip", file=sys.stderr)
        return chosen, zf.read(chosen)


def parse_takeout_json(data: bytes) -> str:
    """Parse Google Takeout JSON. Returns chronological transcript text."""
    items = json.loads(data)
    if not isinstance(items, list):
        raise ValueError(f"Expected JSON array, got {type(items).__name__}")

    entries = []
    for item in items:
        # Takeout entries have keys like: title, time, header, products, details
        ts = item.get("time", "")
        title = item.get("title", "")
        # The actual content varies; "title" often contains the prompt for Bard activity
        # or "Used Bard" with details
        text_blocks = []
        if title:
            text_blocks.append(f"USER: {title}")
        # Some exports have nested 'subtitles' or 'description' with the response
        if "subtitles" in item and isinstance(item["subtitles"], list):
            for s in item["subtitles"]:
                if isinstance(s, dict) and s.get("name"):
                    text_blocks.append(f"GEMINI: {s['name']}")
        if "description" in item:
            text_blocks.append(f"GEMINI: {item['description']}")
        if text_blocks:
            entries.append({"time": ts, "text": "\n".join(text_blocks)})

    entries.sort(key=lambda e: e["time"])
    transcript = []
    for e in entries:
        date_part = e["time"][:10] if e["time"] else "unknown date"
        transcript.append(f"[{date_part}]\n{e['text']}\n")
    return "\n".join(transcript)


class _GeminiHTMLParser(HTMLParser):
    """Parse Takeout MyActivity.html for Bard/Gemini.
    Each activity is in a div.outer-cell containing time + content."""
    def __init__(self):
        super().__init__()
        self.entries: list[dict] = []
        self._current_text = []
        self._in_cell = False
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag == "div" and "outer-cell" in attrs_d.get("class", ""):
            self._in_cell = True
            self._depth = 1
            self._current_text = []
        elif self._in_cell and tag == "div":
            self._depth += 1
        elif self._in_cell and tag == "br":
            self._current_text.append("\n")

    def handle_endtag(self, tag):
        if self._in_cell and tag == "div":
            self._depth -= 1
            if self._depth == 0:
                self._in_cell = False
                text = " ".join("".join(self._current_text).split())
                if text:
                    self.entries.append({"text": text})

    def handle_data(self, data):
        if self._in_cell:
            self._current_text.append(data)


def parse_takeout_html(data: bytes) -> str:
    """Parse Takeout HTML. Returns chronological transcript text."""
    p = _GeminiHTMLParser()
    p.feed(data.decode("utf-8", errors="replace"))
    # entries are already in document order which is reverse-chronological in
    # Takeout. We can't easily extract timestamps without more parsing, so we
    # let the LLM see the order and infer time from content
    return "\n\n---\n\n".join(e["text"] for e in p.entries)


def parse_raw_text(data: bytes) -> str:
    """Treat input as a raw text dump. Caller should ensure entries are
    chronologically ordered with date markers."""
    return data.decode("utf-8", errors="replace")


def load_input(path: Path) -> str:
    """Auto-detect format and return transcript text."""
    suffix = path.suffix.lower()
    if suffix == ".zip":
        name, raw = find_activity_file_in_zip(path)
        if name.endswith(".json"):
            return parse_takeout_json(raw)
        return parse_takeout_html(raw)
    if suffix == ".json":
        return parse_takeout_json(path.read_bytes())
    if suffix in (".html", ".htm"):
        return parse_takeout_html(path.read_bytes())
    if suffix in (".txt", ".md"):
        return parse_raw_text(path.read_bytes())
    raise SystemExit(f"Unsupported file type: {suffix}. Use .zip, .json, .html, or .txt")


# ---------------- distillation ---------------- #

def distill(transcript: str) -> str:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set. Put it in distiller/.env")

    client = anthropic.Anthropic()

    today = datetime.now().strftime("%Y-%m-%d")
    user_msg = (
        f"Today's date: {today}\n\n"
        f"<gemini_history>\n{transcript}\n</gemini_history>\n\n"
        f"按 prompt 中规定的 schema 蒸馏成健身档案，输出只包含 markdown 档案本身。"
    )

    transcript_chars = len(transcript)
    print(f"Transcript size: {transcript_chars:,} chars", file=sys.stderr)

    # System prompt + the prompt.md content; user message holds the transcript.
    # Cache the prompt.md (stable across runs); transcript is volatile.
    print(f"Calling {MODEL} with adaptive thinking...", file=sys.stderr)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")

    print(
        f"Tokens — input: {resp.usage.input_tokens:,}, "
        f"output: {resp.usage.output_tokens:,}, "
        f"cache_read: {getattr(resp.usage, 'cache_read_input_tokens', 0):,}, "
        f"cache_write: {getattr(resp.usage, 'cache_creation_input_tokens', 0):,}",
        file=sys.stderr,
    )

    # Strip leading/trailing fence if model wrapped output
    text = text.strip()
    fence_match = re.match(r"^```(?:markdown)?\s*\n(.*?)\n```\s*$", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)

    return text


# ---------------- main ---------------- #

def main():
    p = argparse.ArgumentParser(description="Distill Gemini chat history into a fitness journal")
    p.add_argument("input", type=Path, help="Path to Takeout export (zip/json/html) or raw text")
    p.add_argument("-o", "--output", type=Path, default=None,
                   help="Output path. Default: stdout")
    p.add_argument("--show-transcript", action="store_true",
                   help="Print parsed transcript to stderr without calling API (debug)")
    args = p.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")

    transcript = load_input(args.input)

    if args.show_transcript:
        print(transcript, file=sys.stderr)
        print(f"\n[--- end transcript ({len(transcript):,} chars) ---]", file=sys.stderr)
        return

    journal = distill(transcript)

    if args.output:
        args.output.write_text(journal, encoding="utf-8")
        print(f"\nWritten to {args.output}", file=sys.stderr)
    else:
        print(journal)


if __name__ == "__main__":
    main()
