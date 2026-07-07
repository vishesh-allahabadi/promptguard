from promptguard.anonymizer import anonymize_text


def test_additional_secret_patterns_are_removed_from_safe_output() -> None:
    samples = [
        "AIzaFAKEgoogleApiKey1234567890abcdefghi",
        "xoxb-" + "123456789012-123456789012-FAKEslackTokenabcd",
        "https://abcdefghijklmnopqrst.supabase.co",
        "re_FAKEresendApiKey1234567890",
        "AC" + "0123456789abcdef0123456789abcdef",
        "TWILIO_AUTH_TOKEN=0123456789abcdef0123456789abcdef",
        "vercel_FAKEvercelToken1234567890",
        "CLOUDFLARE_API_TOKEN=FAKEcloudflareToken1234567890",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtlLXVzZXIiLCJzY29wZSI6InRlc3Qtb25seSJ9.FAKEsignaturePart1234567890abcd",
    ]
    for secret in samples:
        result = anonymize_text(f"Please debug this secret: {secret}")
        assert result.scan.risk_level.value == "CRITICAL"
        assert secret not in result.safe_text
        assert "[SECRET_REMOVED]" in result.safe_text
