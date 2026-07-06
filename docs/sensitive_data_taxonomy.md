# Sensitive Data Taxonomy

PromptGuard uses conservative categories for local prompt scanning.

## Critical

- API keys.
- Password-like assignments.
- Private key blocks.
- Bearer tokens.
- Database connection URLs.
- URLs containing credentials.

## High

- Email addresses.
- Phone numbers.
- IP addresses.
- PAN-like IDs.
- Aadhaar-like IDs.
- Configured customer names.
- Configured client names.
- PII combined with legal, finance, or health context.

## Medium

- Production environment indicators.
- Financial amounts.
- Exact dates.
- Legal, finance, or health keywords without identity data.
- Confidential business keywords.
- Configured company names.

## Low

- Generic code.
- Non-production error descriptions.
- Public technical context with no detected sensitive values.

## Notes

PAN-like and Aadhaar-like detections are pattern matches only. They may produce false positives and should not be treated as verified government ID classification.

