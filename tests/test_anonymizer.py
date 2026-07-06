from promptguard.anonymizer import anonymize_text
from promptguard.types import PromptGuardConfig


def test_anonymization_removes_secrets_and_preserves_context() -> None:
    result = anonymize_text(
        "Production Stripe live key sk_live_FAKEstripeKey1234567890 failed during checkout."
    )
    assert "sk_live_" not in result.safe_text
    assert "payment provider live key [SECRET_REMOVED]" in result.safe_text
    assert "checkout" in result.safe_text


def test_money_generalization_inr_and_usd() -> None:
    inr = anonymize_text("Invoice amount is ₹3,47,220.").safe_text
    usd = anonymize_text("Refund amount is $12,430.").safe_text
    assert "around ₹3.5 lakh" in inr
    assert "around $12k" in usd


def test_date_generalization() -> None:
    result = anonymize_text("The incident happened on 2026-07-04.")
    assert "around July 2026" in result.safe_text


def test_email_phone_database_redaction() -> None:
    result = anonymize_text(
        "Email jane@example.com, call +91 98765 43210, DB postgres://u:p@example.com/app."
    )
    assert "[EMAIL]" in result.safe_text
    assert "[PHONE]" in result.safe_text
    assert "[DATABASE_URL_REMOVED]" in result.safe_text
    assert "jane@example.com" not in result.safe_text
    assert "postgres://" not in result.safe_text


def test_configured_name_anonymization_is_stable() -> None:
    config = PromptGuardConfig(customer_names=("Jane Rao", "Arjun Mehta"), client_names=("Acme Retail",))
    result = anonymize_text("Jane Rao and Arjun Mehta discussed Acme Retail with Jane Rao.", config)
    assert result.safe_text.count("Person A") == 2
    assert "Person B" in result.safe_text
    assert "Client A" in result.safe_text

