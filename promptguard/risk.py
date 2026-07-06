from __future__ import annotations

from .types import Action, Finding, RiskLevel

_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}

PII_CATEGORIES = {
    "email",
    "phone",
    "ip_address",
    "pan_like_id",
    "aadhaar_like_id",
    "customer_name",
}
SENSITIVE_CONTEXT_CATEGORIES = {"legal_context", "financial_context", "health_context"}


def max_risk(levels: list[RiskLevel]) -> RiskLevel:
    if not levels:
        return RiskLevel.LOW
    return max(levels, key=lambda level: _ORDER[level])


def score_risk(findings: tuple[Finding, ...] | list[Finding]) -> RiskLevel:
    if not findings:
        return RiskLevel.LOW

    categories = {finding.category for finding in findings}
    if any(finding.risk is RiskLevel.CRITICAL for finding in findings):
        return RiskLevel.CRITICAL

    base = max_risk([finding.risk for finding in findings])
    if categories & PII_CATEGORIES and categories & SENSITIVE_CONTEXT_CATEGORIES:
        return RiskLevel.HIGH
    if "configured_confidential_term" in categories and (
        categories & PII_CATEGORIES or "production_indicator" in categories
    ):
        return RiskLevel.HIGH
    return base


def recommended_action(risk_level: RiskLevel) -> Action:
    if risk_level is RiskLevel.CRITICAL:
        return Action.BLOCK
    if risk_level is RiskLevel.HIGH:
        return Action.REDACT_FIRST
    if risk_level is RiskLevel.MEDIUM:
        return Action.WARN
    return Action.ALLOW

