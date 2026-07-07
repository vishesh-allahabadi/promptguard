from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .anonymizer import anonymize_text
from .clipboard import PromptGuardClipboardError
from .config import load_config
from .scanner import scan_text
from .types import PromptGuardConfig, RiskLevel
from .workflows import (
    PromptGuardWorkflowError,
    WorkflowResult,
    load_local_workflow_config,
    run_clip_workflow,
    run_compose_workflow,
    run_safe_workflow,
)

HOOK_WRAPPER = '''#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from promptguard.codex_hook import main

if __name__ == "__main__":
    raise SystemExit(main())
'''


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

    safe = subparsers.add_parser("safe")
    safe_source = safe.add_mutually_exclusive_group(required=True)
    safe_source.add_argument("--text")
    safe_source.add_argument("--file")
    safe_source.add_argument("--stdin", action="store_true")
    safe.add_argument("--copy", action="store_true", help="Copy only the safe rewritten prompt.")
    safe.add_argument("--output", help="Write only the safe rewritten prompt to this file.")
    safe.add_argument("--fail-on-block", action="store_true", help="Exit non-zero when policy blocks the prompt.")

    clip = subparsers.add_parser("clip")
    clip.add_argument("--copy", action="store_true", help="Accepted for clarity; clip copies by default.")
    clip.add_argument("--print", dest="print_safe", action="store_true", help="Print the safe rewritten prompt.")
    clip.add_argument("--fail-on-block", action="store_true", help="Exit non-zero when policy blocks the prompt.")

    compose = subparsers.add_parser("compose")
    compose.add_argument("--copy", action="store_true", help="Copy only the safe rewritten prompt.")
    compose.add_argument("--output", help="Write only the safe rewritten prompt to this file.")
    compose.add_argument("--editor", help='Editor command, for example "code --wait".')
    compose.add_argument("--fail-on-block", action="store_true", help="Exit non-zero when policy blocks the prompt.")

    check = subparsers.add_parser("check")
    check.add_argument("--file", required=True)

    subparsers.add_parser("test-examples")
    subparsers.add_parser("install-codex-hook")
    subparsers.add_parser("doctor")

    args = parser.parse_args(argv)
    config = load_config(args.config)

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

    if args.command == "safe":
        workflow_config = load_local_workflow_config(args.config)
        text = _read_safe_source(args)
        return _run_local_command(
            lambda: run_safe_workflow(text, workflow_config, copy=args.copy, output=args.output),
            as_json=args.json,
            fail_on_block=args.fail_on_block,
            print_safe=True,
        )

    if args.command == "clip":
        workflow_config = load_local_workflow_config(args.config)
        return _run_local_command(
            lambda: run_clip_workflow(workflow_config, copy=True),
            as_json=args.json,
            fail_on_block=args.fail_on_block,
            print_safe=args.print_safe,
            prefix="Safe rewritten prompt copied to clipboard.",
        )

    if args.command == "compose":
        workflow_config = load_local_workflow_config(args.config)
        return _run_local_command(
            lambda: run_compose_workflow(
                workflow_config,
                editor=args.editor,
                copy=args.copy,
                output=args.output,
            ),
            as_json=args.json,
            fail_on_block=args.fail_on_block,
            print_safe=True,
        )

    if args.command == "test-examples":
        return _test_examples(config, args.json)

    if args.command == "install-codex-hook":
        return _install_codex_hook()

    if args.command == "doctor":
        return _doctor()

    return 2


def _read_source(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    return Path(args.file).read_text(encoding="utf-8")


def _read_safe_source(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8")
    return sys.stdin.read()


def _run_local_command(
    runner,
    *,
    as_json: bool,
    fail_on_block: bool,
    print_safe: bool,
    prefix: str | None = None,
) -> int:
    try:
        result = runner()
    except (PromptGuardClipboardError, PromptGuardWorkflowError, OSError) as exc:
        if as_json:
            print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1

    if prefix and not as_json:
        print(prefix)
    _print_workflow_result(result, as_json, print_safe=print_safe)
    return 1 if fail_on_block and result.blocked else 0


def _print_workflow_result(result: WorkflowResult, as_json: bool, *, print_safe: bool) -> None:
    payload = result.to_dict()
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("PromptGuard result")
    print(f"risk: {result.risk_level}")
    print(f"policy: {result.policy}")
    print(f"categories: {', '.join(result.categories) if result.categories else 'none'}")
    if print_safe:
        print("\nsafe rewritten prompt:")
        print(result.safe_text)
    print(f"\ncopied_to_clipboard: {str(result.copied_to_clipboard).lower()}")
    if result.output_file:
        print(f"output_file: {result.output_file}")


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


def _install_codex_hook() -> int:
    root = _git_root(Path.cwd())
    codex_dir = root / ".codex"
    hooks_dir = codex_dir / "hooks"
    hooks_json = codex_dir / "hooks.json"
    hook_path = hooks_dir / "promptguard_user_prompt_submit.py"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(HOOK_WRAPPER, encoding="utf-8")
    hook_path.chmod(0o755)

    data: dict[str, Any] = {}
    if hooks_json.exists():
        try:
            data = json.loads(hooks_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    hooks = data.setdefault("hooks", {})
    prompt_hooks = hooks.setdefault("UserPromptSubmit", [])
    command = '/usr/bin/env python3 "$(git rev-parse --show-toplevel)/.codex/hooks/promptguard_user_prompt_submit.py"'
    hook_entry = {
        "type": "command",
        "command": command,
        "statusMessage": "PromptGuard is checking prompt privacy",
    }
    already_present = False
    for group in prompt_hooks:
        for nested in group.get("hooks", []):
            if isinstance(nested, dict) and "promptguard_user_prompt_submit.py" in nested.get("command", ""):
                nested.update(hook_entry)
                already_present = True
    if not already_present:
        prompt_hooks.append({"hooks": [hook_entry]})
    hooks_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"Installed PromptGuard Codex hook at {hook_path}")
    print(f"Updated {hooks_json}")
    print("Codex may require you to review and trust this hook using /hooks before it runs.")
    print("This protects only prompts submitted through Codex in this repo/config layer when hooks are enabled and trusted.")
    return 0


def _doctor() -> int:
    root = _git_root(Path.cwd())
    hooks_json = root / ".codex" / "hooks.json"
    hook_path = root / ".codex" / "hooks" / "promptguard_user_prompt_submit.py"
    config_path = root / ".promptguard.yml"
    print("PromptGuard doctor")
    print(f"version: {_version()}")
    print(f"python_executable: {sys.executable}")
    print(f"python_version: {sys.version.split()[0]}")
    print(f"cwd: {Path.cwd()}")
    print(f"repo_root: {root}")
    print(f"hooks_json_exists: {hooks_json.exists()}")
    print(f"hook_script_exists: {hook_path.exists()}")
    print(f"promptguard_config_exists: {config_path.exists()}")
    print(f"hook_files_present: {hooks_json.exists() and hook_path.exists()}")
    print("Codex may require you to review and trust this hook using /hooks before it runs.")
    return 0 if hooks_json.exists() and hook_path.exists() else 1


def _git_root(cwd: Path) -> Path:
    git = shutil.which("git")
    if git:
        result = subprocess.run(
            [git, "rev-parse", "--show-toplevel"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    return cwd


def _version() -> str:
    try:
        from importlib.metadata import version

        return version("promptguard")
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
