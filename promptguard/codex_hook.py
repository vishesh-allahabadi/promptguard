from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

from .anonymizer import anonymize_text
from .config import effective_block_on, effective_warn_on, load_config
from .types import AnonymizeResult, PromptGuardConfig, RiskLevel


def parse_codex_hook_input(raw: str) -> tuple[str, dict[str, Any]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw, {}
    if isinstance(data, dict):
        prompt = data.get("prompt")
        return prompt if isinstance(prompt, str) else "", data
    return raw, {}


def build_promptguard_decision(prompt: str, config: PromptGuardConfig | None = None) -> dict[str, Any] | None:
    result = anonymize_text(prompt, config)
    risk = result.scan.risk_level
    if risk in effective_block_on(config):
        return {"decision": "block", "reason": format_block_reason(result)}
    if risk in effective_warn_on(config):
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": format_warning_context(result),
            }
        }
    return None


def format_block_reason(result: AnonymizeResult) -> str:
    risk = result.scan.risk_level.value
    categories = "\n".join(f"- {category}" for category in result.scan.categories) or "- none"
    return (
        f"PromptGuard blocked this prompt before it was sent because it contains {risk} sensitive data.\n\n"
        f"Detected risk level: {risk}\n\n"
        f"Detected categories:\n{categories}\n\n"
        f"Safe rewritten prompt:\n{result.safe_text}\n\n"
        "Copy the safe rewritten prompt and submit again, or edit your local .promptguard.yml policy "
        "if you intentionally want a different threshold."
    )


def format_warning_context(result: AnonymizeResult) -> str:
    categories = ", ".join(result.scan.categories) if result.scan.categories else "none"
    return (
        f"PromptGuard warning: {result.scan.risk_level.value} risk content was detected. "
        "Review whether the prompt should be anonymized before sharing sensitive operational context. "
        f"Detected categories: {categories}."
    )


def main(stdin: str | None = None) -> int:
    raw = sys.stdin.read() if stdin is None else stdin
    try:
        prompt, metadata = parse_codex_hook_input(raw)
        config = _load_hook_config(metadata)
        decision = build_promptguard_decision(prompt, config)
        if decision is not None:
            print(json.dumps(decision))
        return 0
    except Exception:
        if os.environ.get("PROMPTGUARD_DEBUG") == "1":
            traceback.print_exc(file=sys.stderr)
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": "PromptGuard could not verify this prompt safely, so it blocked submission.",
                }
            )
        )
        return 0


def _load_hook_config(metadata: dict[str, Any]) -> PromptGuardConfig:
    env_path = os.environ.get("PROMPTGUARD_CONFIG")
    if env_path:
        return load_config(env_path)
    root = _git_root(_metadata_cwd(metadata))
    config_path = root / ".promptguard.yml"
    return load_config(config_path if config_path.exists() else None)


def _metadata_cwd(metadata: dict[str, Any]) -> Path:
    cwd = metadata.get("cwd")
    if isinstance(cwd, str) and cwd:
        return Path(cwd)
    return Path.cwd()


def _git_root(cwd: Path) -> Path:
    git = shutil.which("git")
    if git:
        result = subprocess.run(
            [git, "rev-parse", "--show-toplevel"],
            cwd=cwd if cwd.exists() else Path.cwd(),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    return cwd if cwd.exists() else Path.cwd()

