# PromptGuard

Get useful AI coding help without oversharing secrets or private context.

PromptGuard is a local-first sensitive-data scanner and safe prompt rewriter for developers using AI coding agents such as Codex and Claude Code. It scans prompts before submission, detects risky content, and rewrites the prompt into a safer version while preserving enough context for useful coding help.

> PromptGuard helps reduce sensitive-data exposure but does not guarantee privacy, security, or compliance.

## Why It Exists

AI coding agents are useful for debugging logs, deployment issues, incidents, config files, and customer workflows. Those same prompts can accidentally include API keys, database URLs, customer data, private company context, production logs, legal details, or financial information.

PromptGuard gives developers a local checkpoint before that content is sent anywhere else.

## What It Does

- Scans prompt text locally.
- Detects common secrets, PII, production indicators, financial/legal/health context, and configured names.
- Assigns `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` risk.
- Rewrites prompts with safer placeholders.
- Provides CLI commands and hook templates for coding-agent workflows.
- Avoids external APIs, telemetry, analytics, cloud services, and permanent raw prompt storage.

## See It Working In 20 Seconds

```bash
python -m pip install -e ".[dev]"
promptguard anonymize --text "Production Stripe live key sk_live_FAKEstripeKey1234567890 failed for jane@example.com on invoice $12,430"
```

Expected output conceptually:

```text
risk: CRITICAL
action: block
categories: email, financial_amount, financial_context, production_indicator, stripe_key

safe rewritten prompt:
Production payment provider live key [SECRET_REMOVED] failed for [EMAIL] on invoice around $12k
```

Check a harmless prompt:

```bash
promptguard scan --text "How do I refactor this harmless Python function?"
```

Expected:

```text
risk: LOW
action: allow
categories: none
```

## What It Does Not Do

- It does not guarantee privacy, security, or compliance.
- It does not detect every secret or every type of sensitive data.
- It does not replace secure development practices, DLP, access controls, or legal review.
- It does not validate whether a detected fake-looking token is active.
- It does not send raw prompts to any external service.

## Installation

From the repository root:

```bash
python -m pip install -e .
```

For development:

```bash
python -m pip install -e ".[dev]"
```

## CLI Usage

Scan text:

```bash
promptguard scan --text "My production database URL is postgres://user:pass@example.com/app"
```

Scan a file:

```bash
promptguard scan --file prompt.txt
```

Create a safe rewrite:

```bash
promptguard anonymize --text "Email jane@example.com about invoice $12,430"
```

Check a file and return non-zero for critical findings:

```bash
promptguard check --file prompt.txt
```

Validate bundled examples:

```bash
promptguard test-examples
```

JSON output:

```bash
promptguard --json anonymize --file prompt.txt
```

## Example

Input:

```text
Production Stripe live key sk_live_FAKE1234567890abcdef for jane@example.com is failing.
```

Safe rewrite:

```text
Production payment provider live key [SECRET_REMOVED] for [EMAIL] is failing.
```

Recommended action:

```text
block
```

## Configured Names

Use a local YAML config to flag names that only your organization knows are sensitive:

```yaml
customer_names:
  - Jane Rao
company_names:
  - Internal Labs
client_names:
  - Acme Retail
confidential_terms:
  - Project Sundial
```

Then run:

```bash
promptguard --config examples/promptguard.example.yml anonymize --file prompt.txt
```

## Hook Usage

Hook templates are included for Codex and Claude Code:

- `hooks/codex/hooks.example.json`
- `hooks/codex/promptguard_hook.py`
- `hooks/claude-code/hooks.example.json`
- `hooks/claude-code/promptguard_hook.py`

Exact hook schemas can change. Treat these files as local templates and adapt paths for your installed Codex or Claude Code version.

## Skill Usage

Agent skill templates are included:

- `skills/codex/promptguard/SKILL.md`
- `skills/claude-code/promptguard/SKILL.md`

They instruct an AI coding agent to prefer safe prompt rewriting, avoid requesting raw secrets, and keep sensitive values out of generated files, commits, logs, and examples.

## Privacy Design

- Raw prompt text stays local.
- No external API calls are made.
- No telemetry or analytics are included.
- Raw prompt text is not stored permanently.
- In-memory mappings are only used during a single anonymization run.
- Examples use fake placeholder secrets only.

## Limitations

PromptGuard is deterministic and regex/config based. It can miss secrets, overflag harmless text, or preserve context that is still sensitive. Review safe rewrites before submitting them to another system.

See `docs/limitations.md` for more detail.

## Roadmap

- More configurable patterns.
- Better language-aware redaction.
- Editor integrations.
- Safer diff and log handling.
- Local evaluation reports.
- More hook adapters as coding-agent hook schemas stabilize.

## Contributing

Contributions are welcome when they preserve the project principles:

- No paid APIs.
- No telemetry.
- No cloud backend.
- No permanent raw prompt storage.
- Conservative privacy and security wording.
- Tests for new detectors and anonymizers.

## Security Disclosure

If you find a security issue, please do not open a public issue containing secrets or exploit details. Create a minimal report with safe placeholders and follow the guidance in `SECURITY.md`.
