from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .types import RiskLevel


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def write_bypass_audit_log(
    *,
    root: Path,
    prompt: str,
    risk_level: RiskLevel,
    categories: tuple[str, ...],
    action: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    log_path = root / ".promptguard" / "audit.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_level": risk_level.value,
        "detected_categories": list(categories),
        "action": action,
        "prompt_hash": prompt_hash(prompt),
    }
    context = _audit_context(metadata or {})
    if context:
        record["context"] = context
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return log_path


def _audit_context(metadata: dict[str, Any]) -> dict[str, str]:
    allowed = (
        "hook_event_name",
        "cwd",
        "session_id",
        "turn_id",
        "permission_mode",
        "model",
        "tool",
        "tool_name",
    )
    return {key: value for key in allowed if isinstance((value := metadata.get(key)), str) and value}
