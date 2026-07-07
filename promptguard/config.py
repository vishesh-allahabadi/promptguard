from __future__ import annotations

from pathlib import Path

from .types import PromptGuardConfig, RiskLevel


def load_config(path: str | Path | None) -> PromptGuardConfig:
    if path is None:
        return PromptGuardConfig()
    config_path = Path(path)
    if not config_path.exists():
        return PromptGuardConfig()
    data = parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    return config_from_mapping(data)


def config_from_mapping(data: dict[str, str | list[str]]) -> PromptGuardConfig:
    return PromptGuardConfig(
        mode=_optional_string(data.get("mode")),
        block_on=_risk_tuple(data.get("block_on")),
        warn_on=_risk_tuple(data.get("warn_on")),
        customer_names=_string_tuple(data.get("customer_names")),
        company_names=_string_tuple(data.get("company_names")),
        client_names=_string_tuple(data.get("client_names")),
        confidential_terms=_string_tuple(data.get("confidential_terms")),
    )


def parse_simple_yaml(raw: str) -> dict[str, str | list[str]]:
    data: dict[str, str | list[str]] = {}
    current: str | None = None
    for line in raw.splitlines():
        without_comment = line.split("#", 1)[0].rstrip()
        stripped = without_comment.strip()
        if not stripped:
            continue
        if not line.startswith(" ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = _clean_scalar(value)
                current = None
            else:
                data[key] = []
                current = key
            continue
        if current and stripped.startswith("- "):
            items = data.setdefault(current, [])
            if isinstance(items, list):
                items.append(_clean_scalar(stripped[2:].strip()))
    return data


def _clean_scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _optional_string(value: str | list[str] | None) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _string_tuple(value: str | list[str] | None) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(item for item in value if item)
    if isinstance(value, str) and value:
        return (value,)
    return ()


def _risk_tuple(value: str | list[str] | None) -> tuple[RiskLevel, ...]:
    values = _string_tuple(value)
    risks: list[RiskLevel] = []
    for item in values:
        try:
            risks.append(RiskLevel[item.strip().upper()])
        except KeyError:
            continue
    return tuple(risks)


def effective_block_on(config: PromptGuardConfig | None) -> tuple[RiskLevel, ...]:
    if config and config.block_on:
        return config.block_on
    return (RiskLevel.CRITICAL, RiskLevel.HIGH)


def effective_warn_on(config: PromptGuardConfig | None) -> tuple[RiskLevel, ...]:
    if config and config.warn_on:
        return config.warn_on
    return (RiskLevel.MEDIUM,)

