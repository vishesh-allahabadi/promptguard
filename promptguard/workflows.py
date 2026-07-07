from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .anonymizer import anonymize_text
from .clipboard import copy_text, paste_text
from .config import load_config
from .policy import action_for_risk, is_blocked
from .types import PromptGuardConfig


class PromptGuardWorkflowError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkflowResult:
    risk_level: str
    policy: str
    categories: tuple[str, ...]
    safe_text: str
    copied_to_clipboard: bool = False
    output_file: str | None = None

    @property
    def blocked(self) -> bool:
        return self.policy == "block"

    def to_dict(self) -> dict[str, object]:
        return {
            "risk_level": self.risk_level,
            "policy": self.policy,
            "categories": list(self.categories),
            "safe_text": self.safe_text,
            "copied_to_clipboard": self.copied_to_clipboard,
            "output_file": self.output_file,
        }


def load_local_workflow_config(path: str | Path | None) -> PromptGuardConfig:
    if path is not None:
        return load_config(path)
    discovered = _find_local_config(Path.cwd())
    return load_config(discovered) if discovered else load_config(None)


def run_safe_workflow(
    text: str,
    config: PromptGuardConfig,
    *,
    copy: bool = False,
    output: str | Path | None = None,
) -> WorkflowResult:
    result = anonymize_text(text, config)
    output_file = _write_output(output, result.safe_text)
    copied = False
    if copy:
        copy_text(result.safe_text)
        copied = True
    return WorkflowResult(
        risk_level=result.scan.risk_level.value,
        policy=action_for_risk(result.scan.risk_level, config),
        categories=result.scan.categories,
        safe_text=result.safe_text,
        copied_to_clipboard=copied,
        output_file=output_file,
    )


def run_clip_workflow(
    config: PromptGuardConfig,
    *,
    copy: bool = True,
) -> WorkflowResult:
    text = paste_text()
    if not text:
        raise PromptGuardWorkflowError("Clipboard is empty. Copy prompt text first, then run promptguard clip.")
    return run_safe_workflow(text, config, copy=copy)


def run_compose_workflow(
    config: PromptGuardConfig,
    *,
    editor: str | None = None,
    copy: bool = False,
    output: str | Path | None = None,
) -> WorkflowResult:
    editor_command = _editor_command(editor)
    if not editor_command:
        raise PromptGuardWorkflowError("No editor found. Set $EDITOR or pass --editor.")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".prompt.txt", prefix="promptguard-", delete=False) as handle:
            temp_path = Path(handle.name)
        command = shlex.split(editor_command) + [str(temp_path)]
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            raise PromptGuardWorkflowError(f"Editor exited with code {result.returncode}.")
        text = temp_path.read_text(encoding="utf-8")
        if not text.strip():
            raise PromptGuardWorkflowError("Prompt is empty. No safe prompt was created.")
        return run_safe_workflow(text, config, copy=copy, output=output)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def should_fail_on_block(result: WorkflowResult, config: PromptGuardConfig) -> bool:
    return is_blocked(_risk_from_result(result), config)


def _risk_from_result(result: WorkflowResult):
    from .types import RiskLevel

    return RiskLevel[result.risk_level]


def _write_output(output: str | Path | None, safe_text: str) -> str | None:
    if output is None:
        return None
    path = Path(output)
    path.write_text(safe_text, encoding="utf-8")
    return str(path)


def _find_local_config(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for path in (current, *current.parents):
        candidate = path / ".promptguard.yml"
        if candidate.exists():
            return candidate
        if (path / ".git").exists():
            break
    return None


def _editor_command(editor: str | None) -> str | None:
    if editor:
        return editor
    env_editor = os.environ.get("EDITOR")
    if env_editor:
        return env_editor
    if os.name == "nt":
        return "notepad"
    if shutil.which("nano"):
        return "nano"
    return None
