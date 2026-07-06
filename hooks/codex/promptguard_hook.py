#!/usr/bin/env python3
"""Example Codex prompt hook template.

Exact Codex hook schemas can change. This script accepts plain stdin or a JSON
object containing prompt/text/message fields, scans locally, and blocks critical
findings by exiting non-zero.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from promptguard.anonymizer import anonymize_text  # noqa: E402
from promptguard.types import RiskLevel  # noqa: E402


def _extract_prompt(raw: str) -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    for key in ("prompt", "text", "message", "input"):
        if isinstance(data, dict) and isinstance(data.get(key), str):
            return data[key]
    return raw


def main() -> int:
    raw = sys.stdin.read()
    prompt = _extract_prompt(raw)
    result = anonymize_text(prompt)
    if result.scan.risk_level is RiskLevel.CRITICAL:
        print("PromptGuard blocked this prompt because it contains critical sensitive data.", file=sys.stderr)
        print("\nSafe rewritten version:\n", file=sys.stderr)
        print(result.safe_text, file=sys.stderr)
        return 1
    if result.scan.risk_level.value in {"MEDIUM", "HIGH"}:
        print(f"PromptGuard warning: {result.scan.risk_level.value}. Consider using this safer prompt:", file=sys.stderr)
        print(result.safe_text, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

