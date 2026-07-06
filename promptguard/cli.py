from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .anonymizer import anonymize_text
from .scanner import scan_text
from .types import PromptGuardConfig, RiskLevel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="promptguard", description="Local prompt sensitive-data scanner.")
    parser.add_argument("--config", help="Optional PromptGuard YAML config path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("scan", "anonymize"):
        sub = subparsers.add_parser(command)
        source = sub.add_mutually_exclusive_group(required=True)
        source.add_argument("--text")
        source.add_argument("--file")

    check = subparsers.add_parser("check")
    check.add_argument("--file", required=True)

    subparsers.add_parser("test-examples")

    args = parser.parse_args(argv)
    config = _load_config(args.config)

    if args.command == "scan":
        text = _read_source(args)
        result = scan_text(text, config)
        _print_payload(result.to_dict(), args.json)
        return 1 if result.risk_level is RiskLevel.CRITICAL else 0

    if args.command == "anonymize":
        text = _read_source(args)
        result = anonymize_text(text, config)
        _print_payload(result.to_dict(), args.json)
        return 0

    if args.command == "check":
        text = Path(args.file).read_text(encoding="utf-8")
        result = anonymize_text(text, config)
        _print_payload(result.to_dict(), args.json)
        return 1 if result.scan.risk_level is RiskLevel.CRITICAL else 0

    if args.command == "test-examples":
        return _test_examples(config, args.json)

    return 2


def _read_source(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    return Path(args.file).read_text(encoding="utf-8")


def _load_config(path: str | None) -> PromptGuardConfig:
    if path is None:
        return PromptGuardConfig()
    data = _parse_simple_yaml(Path(path).read_text(encoding="utf-8"))
    return PromptGuardConfig(
        customer_names=tuple(data.get("customer_names", ()) or ()),
        company_names=tuple(data.get("company_names", ()) or ()),
        client_names=tuple(data.get("client_names", ()) or ()),
        confidential_terms=tuple(data.get("confidential_terms", ()) or ()),
    )


def _parse_simple_yaml(raw: str) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    current: str | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and stripped.endswith(":"):
            current = stripped[:-1]
            data[current] = []
            continue
        if current and stripped.startswith("- "):
            value = stripped[2:].strip().strip('"').strip("'")
            data[current].append(value)
    return data


def _print_payload(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    if "risk_level" not in payload:
        for key, value in payload.items():
            print(f"{key}: {value}")
        return

    print(f"risk: {payload['risk_level']}")
    print(f"action: {payload['action']}")
    print(f"categories: {', '.join(payload['categories']) if payload['categories'] else 'none'}")
    if "safe_text" in payload:
        print("\nsafe rewritten prompt:")
        print(payload["safe_text"])


def _test_examples(config: PromptGuardConfig, as_json: bool) -> int:
    root = Path(__file__).resolve().parent.parent
    examples_path = root / "examples" / "risky_prompts.jsonl"
    failures: list[dict[str, Any]] = []
    count = 0
    for line in examples_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        count += 1
        example = json.loads(line)
        result = anonymize_text(example["input"], config)
        categories = set(result.scan.categories)
        expected_categories = set(example["expected_categories"])
        if result.scan.risk_level.value != example["expected_risk_level"]:
            failures.append({"id": example["id"], "reason": "risk", "actual": result.scan.risk_level.value})
        missing = expected_categories - categories
        if missing:
            failures.append({"id": example["id"], "reason": "categories", "missing": sorted(missing)})
        expected_safe = example.get("expected_anonymized_contains", [])
        for phrase in expected_safe:
            if phrase not in result.safe_text:
                failures.append({"id": example["id"], "reason": "safe_text", "missing": phrase})

    payload = {"examples": count, "failures": failures, "passed": not failures}
    _print_payload(payload, as_json)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
