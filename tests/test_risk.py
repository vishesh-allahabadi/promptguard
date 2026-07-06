from promptguard.scanner import scan_text
from promptguard.types import RiskLevel


def test_pii_with_legal_context_escalates_to_high() -> None:
    result = scan_text("Send legal notice update to jane@example.com.")
    assert result.risk_level is RiskLevel.HIGH
    assert result.action.value == "redact-first"


def test_pii_with_finance_context_escalates_to_high() -> None:
    result = scan_text("Invoice for customer jane@example.com has refund $1,250.")
    assert result.risk_level is RiskLevel.HIGH
    assert result.action.value == "redact-first"


def test_finance_context_without_identity_is_medium() -> None:
    result = scan_text("Revenue report shows $12,430 in refunds.")
    assert result.risk_level is RiskLevel.MEDIUM
    assert result.action.value == "warn"

