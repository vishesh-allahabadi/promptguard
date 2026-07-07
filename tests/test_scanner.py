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


def test_detects_additional_secret_patterns() -> None:
    samples = {
        "google_api_key": "AIzaFAKEgoogleApiKey1234567890abcdefghi",
        "slack_token": "xoxb-" + "123456789012-123456789012-FAKEslackTokenabcd",
        "supabase_key_or_url": "https://abcdefghijklmnopqrst.supabase.co",
        "resend_api_key": "re_FAKEresendApiKey1234567890",
        "twilio_account_sid": "AC" + "0123456789abcdef0123456789abcdef",
        "twilio_auth_token_like": "TWILIO_AUTH_TOKEN=0123456789abcdef0123456789abcdef",
        "vercel_token": "vercel_FAKEvercelToken1234567890",
        "cloudflare_api_token": "CLOUDFLARE_API_TOKEN=FAKEcloudflareToken1234567890",
        "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtlLXVzZXIiLCJzY29wZSI6InRlc3Qtb25seSJ9.FAKEsignaturePart1234567890abcd",
    }
    for category, text in samples.items():
        result = scan_text(text)
        assert category in result.categories
        assert result.risk_level is RiskLevel.CRITICAL
        assert result.action.value == "block"


def test_additional_secret_patterns_do_not_flag_harmless_code_as_critical() -> None:
    text = """
def build_url(host):
    return f"https://{host}.example.com"

parts = "header.payload"
token_prefix = "vercel"
cloudflare = {"enabled": False}
"""
    result = scan_text(text)
    assert result.risk_level is RiskLevel.LOW
