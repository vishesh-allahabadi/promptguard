from promptguard.scanner import scan_text
from promptguard.types import PromptGuardConfig, RiskLevel


def categories(text: str) -> set[str]:
    return set(scan_text(text).categories)


def test_detects_major_secret_types() -> None:
    samples = {
        "openai_api_key": "sk-FAKEopenaiKey1234567890abcd",
        "anthropic_api_key": "sk-ant-FAKEanthropicKey1234567890abcd",
        "github_token": "ghp_FAKEgithubToken1234567890abcdef",
        "stripe_key": "sk_live_FAKEstripeKey1234567890",
        "aws_access_key_id": "AKIAFAKEKEY123456789",
        "bearer_token": "Authorization: Bearer fakeBearerToken1234567890abcdef",
        "database_url": "postgres://admin:fakepass@db.example.com:5432/app",
        "password_assignment": "password=fakePassword123",
        "private_key_block": "-----BEGIN PRIVATE KEY-----\nFAKE\n-----END PRIVATE KEY-----",
    }
    for category, text in samples.items():
        result = scan_text(text)
        assert category in result.categories
        assert result.risk_level is RiskLevel.CRITICAL
        assert result.action.value == "block"


def test_detects_pii_and_identity_like_patterns() -> None:
    text = "Email jane@example.com, phone +91 98765 43210, IP 192.168.1.1, PAN ABCDE1234F, ID 1234 5678 9012"
    found = categories(text)
    assert {"email", "phone", "ip_address", "pan_like_id", "aadhaar_like_id"} <= found


def test_no_false_critical_on_harmless_code() -> None:
    text = "def add(a, b):\n    return a + b\nprint(add(2, 3))"
    result = scan_text(text)
    assert result.risk_level is RiskLevel.LOW
    assert result.action.value == "allow"
    assert result.categories == ()


def test_configured_names_are_detected() -> None:
    config = PromptGuardConfig(
        customer_names=("Jane Rao",),
        company_names=("Internal Labs",),
        client_names=("Acme Retail",),
        confidential_terms=("Project Sundial",),
    )
    result = scan_text("Jane Rao at Acme Retail discussed Project Sundial with Internal Labs.", config)
    assert {"customer_name", "client_name", "company_name", "configured_confidential_term"} <= set(result.categories)
    assert result.risk_level is RiskLevel.HIGH

