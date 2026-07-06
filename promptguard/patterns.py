from __future__ import annotations

import re

from .types import PatternRule, PromptGuardConfig, RiskLevel


SECRET_RULES: tuple[PatternRule, ...] = (
    PatternRule(
        "anthropic_api_key",
        "Anthropic-style API key",
        r"\bsk-ant-[A-Za-z0-9_-]{20,}\b",
        RiskLevel.CRITICAL,
        "[SECRET_REMOVED]",
    ),
    PatternRule(
        "openai_api_key",
        "OpenAI-style API key",
        r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
        RiskLevel.CRITICAL,
        "[SECRET_REMOVED]",
    ),
    PatternRule(
        "github_token",
        "GitHub token",
        r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b",
        RiskLevel.CRITICAL,
        "[SECRET_REMOVED]",
    ),
    PatternRule(
        "stripe_key",
        "Stripe API key",
        r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{16,}\b",
        RiskLevel.CRITICAL,
        "[SECRET_REMOVED]",
    ),
    PatternRule(
        "aws_access_key_id",
        "AWS access key ID",
        r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        RiskLevel.CRITICAL,
        "[SECRET_REMOVED]",
    ),
    PatternRule(
        "private_key_block",
        "Private key block",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
        RiskLevel.CRITICAL,
        "[SECRET_REMOVED]",
    ),
    PatternRule(
        "database_url",
        "Database connection URL",
        r"\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)://[^\s'\"<>]+",
        RiskLevel.CRITICAL,
        "[DATABASE_URL_REMOVED]",
    ),
    PatternRule(
        "password_assignment",
        "Password-like assignment",
        r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|token)\b\s*[:=]\s*['\"]?[^'\"\s]{6,}",
        RiskLevel.CRITICAL,
        "[SECRET_REMOVED]",
    ),
    PatternRule(
        "bearer_token",
        "Bearer token",
        r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}",
        RiskLevel.CRITICAL,
        "Bearer [SECRET_REMOVED]",
    ),
    PatternRule(
        "url_with_credentials",
        "URL with credentials",
        r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^@\s/]+@[^\s]+",
        RiskLevel.CRITICAL,
        "[URL_WITH_CREDENTIALS_REMOVED]",
    ),
)

PII_RULES: tuple[PatternRule, ...] = (
    PatternRule(
        "email",
        "Email address",
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        RiskLevel.HIGH,
        "[EMAIL]",
    ),
    PatternRule(
        "ip_address",
        "IP address",
        r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b",
        RiskLevel.HIGH,
        "[IP_ADDRESS]",
    ),
    PatternRule(
        "pan_like_id",
        "PAN-like ID",
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        RiskLevel.HIGH,
        "[PAN_LIKE_ID]",
    ),
    PatternRule(
        "aadhaar_like_id",
        "Aadhaar-like ID",
        r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)",
        RiskLevel.HIGH,
        "[AADHAAR_LIKE_ID]",
    ),
    PatternRule(
        "phone",
        "Phone number",
        r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\d{5}[-.\s]?\d{5}|\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})(?!\w)",
        RiskLevel.HIGH,
        "[PHONE]",
    ),
)

CONTEXT_RULES: tuple[PatternRule, ...] = (
    PatternRule(
        "production_indicator",
        "Production environment indicator",
        r"(?i)\b(?:prod|production|live environment|live key|live database|customer database)\b",
        RiskLevel.MEDIUM,
        "",
    ),
    PatternRule(
        "financial_context",
        "Financial context keyword",
        r"(?i)\b(?:invoice|revenue|salary|payroll|bank account|valuation|profit|loss|margin|refund|chargeback|payment|financial)\b",
        RiskLevel.MEDIUM,
        "",
    ),
    PatternRule(
        "health_context",
        "Health context keyword",
        r"(?i)\b(?:diagnosis|patient|medical|health|prescription|clinic|treatment|symptom|blood report)\b",
        RiskLevel.MEDIUM,
        "",
    ),
    PatternRule(
        "legal_context",
        "Legal context keyword",
        r"(?i)\b(?:contract|lawsuit|legal notice|nda|settlement|compliance|breach|attorney|lawyer)\b",
        RiskLevel.MEDIUM,
        "",
    ),
    PatternRule(
        "confidential_business_keyword",
        "Confidential business keyword",
        r"(?i)\b(?:confidential|internal only|trade secret|board deck|pricing model|private roadmap|acquisition target)\b",
        RiskLevel.MEDIUM,
        "",
    ),
)

VALUE_RULES: tuple[PatternRule, ...] = (
    PatternRule(
        "financial_amount",
        "Financial amount",
        r"(?<!\w)(?:₹\s?\d[\d,]*(?:\.\d+)?|\$\s?\d[\d,]*(?:\.\d+)?|USD\s?\d[\d,]*(?:\.\d+)?|INR\s?\d[\d,]*(?:\.\d+)?)(?!\w)",
        RiskLevel.MEDIUM,
        "[AMOUNT]",
    ),
    PatternRule(
        "date",
        "Exact date",
        r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
        RiskLevel.MEDIUM,
        "[DATE]",
        re.IGNORECASE,
    ),
)

ALL_RULES: tuple[PatternRule, ...] = SECRET_RULES + PII_RULES + CONTEXT_RULES + VALUE_RULES


def configured_rules(config: PromptGuardConfig | None) -> tuple[PatternRule, ...]:
    if config is None:
        return ()

    rules: list[PatternRule] = []
    for category, names, replacement, risk in (
        ("customer_name", config.customer_names, "[PERSON]", RiskLevel.HIGH),
        ("company_name", config.company_names, "[COMPANY]", RiskLevel.MEDIUM),
        ("client_name", config.client_names, "[CLIENT]", RiskLevel.HIGH),
        ("configured_confidential_term", config.confidential_terms, "", RiskLevel.HIGH),
    ):
        for name in names:
            clean = name.strip()
            if not clean:
                continue
            rules.append(
                PatternRule(
                    category,
                    f"Configured {category.replace('_', ' ')}",
                    rf"\b{re.escape(clean)}\b",
                    risk,
                    replacement,
                    re.IGNORECASE,
                )
            )
    return tuple(rules)
