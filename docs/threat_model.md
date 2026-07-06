# Threat Model

PromptGuard helps reduce sensitive-data exposure before developers submit prompts to AI coding agents.

## Assets

- API keys and tokens.
- Database URLs and credentials.
- Customer, employee, patient, legal, or financial data.
- Production logs and operational details.
- Confidential business context.
- Private repository information.

## In Scope

- Local prompt scanning.
- Local prompt rewriting.
- CLI usage.
- Hook-template usage for Codex and Claude Code.
- Deterministic regex and config-based detection.

## Out of Scope

- Full DLP coverage.
- Compliance guarantees.
- Classification of every possible sensitive data type.
- Cloud scanning.
- Validation that a token is active.
- Protection after a user manually bypasses warnings.

## Main Risks

- A prompt contains a secret and is sent to an external model.
- A prompt contains customer PII combined with logs or business context.
- A generated file, commit, or example accidentally preserves raw sensitive values.
- A hook integration misses a prompt because local schemas changed.

## Controls

- Critical findings recommend blocking.
- High-risk findings recommend redaction first.
- Safe rewrites preserve engineering context while removing exact values.
- Hook templates fail closed for critical findings.
- Documentation avoids claims of complete protection.

