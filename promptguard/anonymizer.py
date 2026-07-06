from __future__ import annotations

import re
from datetime import datetime

from .scanner import scan_text
from .types import AnonymizeResult, Finding, PromptGuardConfig


def anonymize_text(text: str, config: PromptGuardConfig | None = None) -> AnonymizeResult:
    scan = scan_text(text, config)
    safe_text = text
    mapping: dict[str, str] = {}

    for finding in sorted(scan.findings, key=lambda item: item.start, reverse=True):
        original = text[finding.start : finding.end]
        replacement = _replacement_for(original, finding, mapping)
        safe_text = safe_text[: finding.start] + replacement + safe_text[finding.end :]

    safe_text = _rewrite_sensitive_phrases(safe_text)
    return AnonymizeResult(scan=scan, safe_text=safe_text, mapping_count=len(mapping))


def _replacement_for(original: str, finding: Finding, mapping: dict[str, str]) -> str:
    if finding.category == "financial_amount":
        return _generalize_money(original)
    if finding.category == "date":
        return _generalize_date(original)
    if finding.category == "customer_name":
        return _stable_label(original, mapping, "Person")
    if finding.category == "company_name":
        return _stable_label(original, mapping, "Company")
    if finding.category == "client_name":
        return _stable_label(original, mapping, "Client")
    if finding.category == "email":
        return "[EMAIL]"
    if finding.category == "phone":
        return "[PHONE]"
    if finding.category == "database_url":
        return "[DATABASE_URL_REMOVED]"
    if finding.replacement:
        return finding.replacement
    return original


def _stable_label(original: str, mapping: dict[str, str], prefix: str) -> str:
    key = original.lower()
    if key not in mapping:
        suffix = chr(ord("A") + len([value for value in mapping.values() if value.startswith(prefix)]))
        mapping[key] = f"{prefix} {suffix}"
    return mapping[key]


def _generalize_money(value: str) -> str:
    compact = value.replace(",", "").replace(" ", "")
    currency = "₹" if "₹" in value or compact.upper().startswith("INR") else "$"
    number_match = re.search(r"\d+(?:\.\d+)?", compact)
    if not number_match:
        return "[AMOUNT]"
    amount = float(number_match.group(0))
    if currency == "₹" and amount >= 100000:
        lakh = amount / 100000
        return f"around ₹{lakh:.1f} lakh"
    if amount >= 1000:
        thousands = amount / 1000
        if thousands >= 10:
            return f"around {currency}{thousands:.0f}k"
        return f"around {currency}{thousands:.1f}k"
    return f"around {currency}{amount:.0f}"


def _generalize_date(value: str) -> str:
    parsers = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y", "%b %d, %Y", "%B %d, %Y")
    for fmt in parsers:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("around %B %Y")
        except ValueError:
            continue
    return "[DATE]"


def _rewrite_sensitive_phrases(text: str) -> str:
    text = re.sub(r"(?i)\bStripe\s+live\s+key\b", "payment provider live key", text)
    text = re.sub(r"(?i)\bOpenAI\s+(?:api\s+)?key\b", "AI provider key", text)
    text = re.sub(r"(?i)\bAnthropic\s+(?:api\s+)?key\b", "AI provider key", text)
    return text

