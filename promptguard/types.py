from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Action(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    REDACT_FIRST = "redact-first"


@dataclass(frozen=True)
class PromptGuardConfig:
    mode: str | None = None
    block_on: tuple[RiskLevel, ...] = ()
    warn_on: tuple[RiskLevel, ...] = ()
    customer_names: tuple[str, ...] = ()
    company_names: tuple[str, ...] = ()
    client_names: tuple[str, ...] = ()
    confidential_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class PatternRule:
    category: str
    label: str
    regex: str
    risk: RiskLevel
    replacement: str
    flags: int = 0
    description: str = ""


@dataclass(frozen=True)
class Finding:
    category: str
    label: str
    start: int
    end: int
    line: int
    column: int
    risk: RiskLevel
    replacement: str
    sample: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScanResult:
    risk_level: RiskLevel
    action: Action
    categories: tuple[str, ...]
    findings: tuple[Finding, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "action": self.action.value,
            "categories": list(self.categories),
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class AnonymizeResult:
    scan: ScanResult
    safe_text: str
    mapping_count: int

    def to_dict(self) -> dict[str, Any]:
        data = self.scan.to_dict()
        data["safe_text"] = self.safe_text
        data["mapping_count"] = self.mapping_count
        return data
