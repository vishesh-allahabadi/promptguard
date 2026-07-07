from __future__ import annotations

from .config import effective_block_on, effective_warn_on
from .types import PromptGuardConfig, RiskLevel


def action_for_risk(risk: RiskLevel, config: PromptGuardConfig | None = None) -> str:
    if is_blocked(risk, config):
        return "block"
    if is_warned(risk, config):
        return "warn"
    return "allow"


def is_blocked(risk: RiskLevel, config: PromptGuardConfig | None = None) -> bool:
    return risk in effective_block_on(config)


def is_warned(risk: RiskLevel, config: PromptGuardConfig | None = None) -> bool:
    return risk in effective_warn_on(config)
