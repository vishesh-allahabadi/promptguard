from __future__ import annotations

from pathlib import Path
from typing import Any

from .types import BypassConfig, PromptGuardConfig, RiskLevel


ConfigValue = Any


def load_config(path: str | Path | None) -> PromptGuardConfig:
    if path is None:
        return PromptGuardConfig()
    config_path = Path(path)
    if not config_path.exists():
        return PromptGuardConfig()
    data = parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    return config_from_mapping(data)


def config_from_mapping(data: dict[str, ConfigValue]) -> PromptGuardConfig:
    return PromptGuardConfig(
        mode=_optional_string(data.get("mode")),
        block_on=_risk_tuple(data.get("block_on")),
        warn_on=_risk_tuple(data.get("warn_on")),
        bypass=_bypass_config(data.get("bypass")),
        customer_names=_string_tuple(data.get("customer_names")),
        company_names=_string_tuple(data.get("company_names")),
        client_names=_string_tuple(data.get("client_names")),
        confidential_terms=_string_tuple(data.get("confidential_terms")),
    )


def parse_simple_yaml(raw: str) -> dict[str, ConfigValue]:
    data: dict[str, ConfigValue] = {}
    current: str | None = None
    current_nested: str | None = None
    current_nested_list: str | None = None
    for line in raw.splitlines():
        without_comment = line.split("#", 1)[0].rstrip()
        stripped = without_comment.strip()
        if not stripped:
            continue
        if not line.startswith(" ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_nested = None
            current_nested_list = None
            if value:
                data[key] = _clean_scalar(value)
                current = None
            else:
                data[key] = []
                current = key
            continue
        if current and line.startswith("  ") and not line.startswith("    ") and ":" in stripped:
            nested_items = data.get(current)
            if not isinstance(nested_items, dict):
                nested_items = {}
                data[current] = nested_items
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_nested = current
            if value:
                nested_items[key] = _clean_scalar(value)
                current_nested_list = None
            else:
                nested_items[key] = []
                current_nested_list = key
            continue
        if current_nested and current_nested_list and stripped.startswith("- "):
            nested_items = data.get(current_nested)
            if isinstance(nested_items, dict):
                items = nested_items.setdefault(current_nested_list, [])
                if isinstance(items, list):
                    items.append(_clean_scalar(stripped[2:].strip()))
            continue
        if current and stripped.startswith("- "):
            items = data.setdefault(current, [])
            if isinstance(items, list):
                items.append(_clean_scalar(stripped[2:].strip()))
    return data


def _clean_scalar(value: str) -> str | bool:
    cleaned = value.strip().strip('"').strip("'")
    lowered = cleaned.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return cleaned


def _optional_string(value: ConfigValue | None) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _string_tuple(value: ConfigValue | None) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(item for item in value if item)
    if isinstance(value, str) and value:
        return (value,)
    return ()


def _risk_tuple(value: ConfigValue | None) -> tuple[RiskLevel, ...]:
    values = _string_tuple(value)
    risks: list[RiskLevel] = []
    for item in values:
        try:
            risks.append(RiskLevel[item.strip().upper()])
        except KeyError:
            continue
    return tuple(risks)


def _optional_bool(value: ConfigValue | None, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return default


def _bypass_config(value: ConfigValue | None) -> BypassConfig:
    if not isinstance(value, dict):
        return BypassConfig()
    return BypassConfig(
        enabled=_optional_bool(value.get("enabled")),
        allow_levels=_risk_tuple(value.get("allow_levels")),
        require_confirmation_for=_risk_tuple(value.get("require_confirmation_for")),
        allow_critical_bypass=_optional_bool(value.get("allow_critical_bypass")),
        audit_log=_optional_bool(value.get("audit_log")),
    )


def effective_block_on(config: PromptGuardConfig | None) -> tuple[RiskLevel, ...]:
    if config and config.block_on:
        return config.block_on
    return (RiskLevel.CRITICAL, RiskLevel.HIGH)


def effective_warn_on(config: PromptGuardConfig | None) -> tuple[RiskLevel, ...]:
    if config and config.warn_on:
        return config.warn_on
    return (RiskLevel.MEDIUM,)
