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
from .audit import write_bypass_audit_log
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


def build_promptguard_decision(
    prompt: str,
    config: PromptGuardConfig | None = None,
    *,
    metadata: dict[str, Any] | None = None,
    audit_root: Path | None = None,
) -> dict[str, Any] | None:
    result = anonymize_text(prompt, config)
    risk = result.scan.risk_level
    if risk in effective_block_on(config):
        bypass_status = bypass_request_status(risk, config, metadata or {})
        if bypass_status == "allowed":
            if config and config.bypass.audit_log and audit_root is not None:
                write_bypass_audit_log(
                    root=audit_root,
                    prompt=prompt,
                    risk_level=risk,
                    categories=result.scan.categories,
                    action="bypass_once",
                    metadata=metadata,
                )
            return None
        return {"decision": "block", "reason": format_block_reason(result, config, bypass_status)}
    if risk in effective_warn_on(config):
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": format_warning_context(result),
            }
        }
    return None


def bypass_request_status(
    risk: RiskLevel,
    config: PromptGuardConfig | None,
    metadata: dict[str, Any],
) -> str:
    bypass = config.bypass if config else None
    if not bypass or not bypass.enabled:
        return "disabled"
    if risk is RiskLevel.CRITICAL and not bypass.allow_critical_bypass:
        return "critical_disabled"
    if risk not in bypass.allow_levels:
        return "level_not_allowed"
    if not _truthy(metadata.get("promptguard_bypass")):
        return "available"
    if _requires_bypass_phrase(risk, config) and metadata.get("promptguard_bypass_confirmation") != "BYPASS":
        return "needs_bypass_phrase"
    return "allowed"


def format_block_reason(
    result: AnonymizeResult,
    config: PromptGuardConfig | None = None,
    bypass_status: str | None = None,
) -> str:
    risk = result.scan.risk_level.value
    categories = "\n".join(f"- {category}" for category in result.scan.categories) or "- none"
    return (
        f"PromptGuard blocked this prompt before it was sent because it contains {risk} sensitive data.\n\n"
        f"Detected risk level: {risk}\n\n"
        f"Detected categories:\n{categories}\n\n"
        f"Safe rewritten prompt:\n{result.safe_text}\n\n"
        f"{format_block_actions(result.scan.risk_level, config, bypass_status)}"
    )


def format_block_actions(
    risk: RiskLevel,
    config: PromptGuardConfig | None = None,
    bypass_status: str | None = None,
) -> str:
    lines = [
        "Action options:",
        "1. Use safe rewritten prompt: copy the rewritten prompt above and submit that instead.",
    ]
    status = bypass_status or bypass_request_status(risk, config, {})
    if status in {"available", "needs_bypass_phrase"}:
        lines.append(
            "2. Bypass once: only for this prompt execution. This may send sensitive data to the AI tool."
        )
        if _requires_bypass_phrase(risk, config):
            lines.append('   To confirm HIGH or CRITICAL risk bypass, type exactly "BYPASS".')
        else:
            lines.append("   Confirm that you understand the prompt may contain sensitive data.")
        if status == "needs_bypass_phrase":
            lines.append('   The bypass request was not accepted because confirmation must be exactly "BYPASS".')
    elif status == "critical_disabled":
        lines.append(
            "2. Bypass once: unavailable for CRITICAL risk because allow_critical_bypass is false."
        )
    elif status == "level_not_allowed":
        lines.append(f"2. Bypass once: unavailable because {risk.value} is not in bypass.allow_levels.")
    else:
        lines.append("2. Bypass once: unavailable because bypass.enabled is false.")
    lines.append(
        "3. Edit policy / policy instructions: update your local .promptguard.yml only if your policy should change."
    )
    return "\n".join(lines)


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
        decision = build_promptguard_decision(prompt, config, metadata=metadata, audit_root=_hook_root(metadata))
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


def _hook_root(metadata: dict[str, Any]) -> Path:
    return _git_root(_metadata_cwd(metadata))


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


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _requires_bypass_phrase(risk: RiskLevel, config: PromptGuardConfig | None) -> bool:
    if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        return True
    return bool(config and risk in config.bypass.require_confirmation_for)
