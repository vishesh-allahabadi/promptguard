from promptguard.config import effective_block_on, effective_warn_on, load_config, parse_simple_yaml
from promptguard.types import RiskLevel


def test_parse_simple_yaml_supports_scalars_and_lists() -> None:
    data = parse_simple_yaml(
        """
mode: strict
block_on:
  - CRITICAL
  - HIGH
warn_on:
  - MEDIUM
customer_names:
  - Rahul Sharma
"""
    )
    assert data["mode"] == "strict"
    assert data["block_on"] == ["CRITICAL", "HIGH"]
    assert data["warn_on"] == ["MEDIUM"]
    assert data["customer_names"] == ["Rahul Sharma"]


def test_load_config_supports_policy_fields(tmp_path) -> None:
    path = tmp_path / ".promptguard.yml"
    path.write_text(
        """
mode: strict
block_on:
  - CRITICAL
warn_on:
  - HIGH
  - MEDIUM
client_names:
  - Acme Retail
""",
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.mode == "strict"
    assert config.block_on == (RiskLevel.CRITICAL,)
    assert config.warn_on == (RiskLevel.HIGH, RiskLevel.MEDIUM)
    assert config.client_names == ("Acme Retail",)


def test_hook_policy_defaults() -> None:
    config = load_config(None)
    assert effective_block_on(config) == (RiskLevel.CRITICAL, RiskLevel.HIGH)
    assert effective_warn_on(config) == (RiskLevel.MEDIUM,)

