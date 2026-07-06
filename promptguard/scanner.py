from __future__ import annotations

import re

from .patterns import ALL_RULES, configured_rules
from .risk import recommended_action, score_risk
from .types import Finding, PatternRule, PromptGuardConfig, ScanResult


def _line_column(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    last_newline = text.rfind("\n", 0, index)
    column = index + 1 if last_newline == -1 else index - last_newline
    return line, column


def _safe_sample(value: str, category: str) -> str:
    if category in {"financial_amount", "date"}:
        return value
    return f"[{category.upper()}]"


def _iter_findings(text: str, rule: PatternRule) -> list[Finding]:
    findings: list[Finding] = []
    for match in re.finditer(rule.regex, text, rule.flags):
        start, end = match.span()
        line, column = _line_column(text, start)
        findings.append(
            Finding(
                category=rule.category,
                label=rule.label,
                start=start,
                end=end,
                line=line,
                column=column,
                risk=rule.risk,
                replacement=rule.replacement,
                sample=_safe_sample(match.group(0), rule.category),
            )
        )
    return findings


def scan_text(text: str, config: PromptGuardConfig | None = None) -> ScanResult:
    findings: list[Finding] = []
    for rule in ALL_RULES + configured_rules(config):
        findings.extend(_iter_findings(text, rule))

    findings.sort(key=lambda finding: (finding.start, -(finding.end - finding.start), finding.category))
    deduped = _dedupe_overlaps(findings)
    risk_level = score_risk(tuple(deduped))
    categories = tuple(sorted({finding.category for finding in deduped}))
    return ScanResult(
        risk_level=risk_level,
        action=recommended_action(risk_level),
        categories=categories,
        findings=tuple(deduped),
    )


def _dedupe_overlaps(findings: list[Finding]) -> list[Finding]:
    priority = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
    kept: list[Finding] = []
    for finding in findings:
        overlaps = [
            existing
            for existing in kept
            if not (finding.end <= existing.start or finding.start >= existing.end)
        ]
        if not overlaps:
            kept.append(finding)
            continue
        strongest = max(
            overlaps + [finding],
            key=lambda item: (priority[item.risk.value], item.end - item.start),
        )
        if strongest is finding:
            kept = [
                existing
                for existing in kept
                if finding.end <= existing.start or finding.start >= existing.end
            ]
            kept.append(finding)
    kept.sort(key=lambda item: item.start)
    return kept
