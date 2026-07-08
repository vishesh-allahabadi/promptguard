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

## Install PromptGuard on Codex / Claude Code

PromptGuard can be installed as a coding-agent pre-submit hook so prompts are scanned before they are sent to Codex, Claude Code, or another agent. The hook blocks risky prompts, rewrites sensitive prompts with safe placeholders, and can support controlled one-time bypass for `LOW`, `MEDIUM`, and `HIGH` risks when enabled.

`CRITICAL` bypass is disabled by default. Audit logs store metadata and prompt hashes only, not raw prompts or secrets.

For the full Codex and Claude Code hook guide, see `docs/coding-agent-hooks.md`.

### Copy-paste setup prompt

Paste this into Codex or Claude Code from inside your project repository:

````text
Install PromptGuard as a pre-submit safety hook for this coding agent.

PromptGuard source:
https://github.com/vishesh-allahabadi/promptguard

Requirements:
- If PromptGuard is not already installed, clone or install it from the source repository above.
- Detect and block sensitive data before prompts are sent.
- Rewrite unsafe prompts by replacing secrets with safe placeholders.
- Do not log raw prompts or secrets.
- Store audit logs with metadata and prompt hashes only.
- Keep local policy in `.promptguard.yml`.
- Keep `.promptguard/audit.log` ignored by git.
- Enable controlled one-time bypass for LOW, MEDIUM, and HIGH risks only.
- Keep CRITICAL bypass disabled by default.
- After installation, run the test suite or the closest available verification command.
- Show me the exact files changed and the final hook status.

Use this safer default config:

```yaml
bypass:
  enabled: true
  allow_levels:
    - LOW
    - MEDIUM
    - HIGH
  require_confirmation_for:
    - HIGH
    - CRITICAL
  allow_critical_bypass: false
  audit_log: true
```

Do not push anything to remote.
````

### Recommended default bypass policy

With bypass enabled, `LOW`, `MEDIUM`, and `HIGH` findings may be bypassed once if the local policy allows that risk level. `HIGH` requires the user to type exactly `BYPASS`.

`CRITICAL` findings remain blocked unless a user explicitly opts into critical bypass. The recommended setting is:

```yaml
allow_critical_bypass: false
```

### Audit log safety

The audit log path is `.promptguard/audit.log`, and it should be ignored by git. Audit logs should contain metadata only:

- timestamp
- risk level
- categories
- action
- prompt hash
- tool/context if available

Audit logs must not contain raw prompt text or secrets.

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

## Safer Local Workflows

PromptGuard protects you only when it runs before the prompt reaches an AI tool. These commands help you scan and rewrite prompts locally before pasting them into Codex, Claude Code, ChatGPT, Cursor, or any other LLM tool.

Recommended workflow:

1. Write the risky prompt locally.
2. Run PromptGuard.
3. Copy only the safe rewritten prompt.
4. Paste the safe prompt into Codex or another LLM tool.

Safe rewrite from text:

```bash
promptguard safe --text "Production Stripe live key sk_live_FAKEstripeKey1234567890 failed for jane@example.com"
```

Safe rewrite from file and copy only the safe prompt:

```bash
promptguard safe --file risky_prompt.txt --copy
```

Read from stdin:

```bash
cat risky_prompt.txt | promptguard safe --stdin
```

Write only the safe rewritten prompt to a file:

```bash
promptguard safe --file risky_prompt.txt --output safe_prompt.txt
```

Scan the current clipboard and replace it with the safe rewritten prompt:

```bash
promptguard clip
```

Compose a prompt in your local editor and copy only the safe rewrite:

```bash
promptguard compose --copy
```

Use a specific editor:

```bash
promptguard compose --editor "code --wait" --copy
```

Fail non-zero when local policy blocks the prompt:

```bash
promptguard safe --text "Email jane@example.com" --fail-on-block
```

`safe --copy` copies only `safe_text`, never the raw prompt. `clip` replaces the clipboard with `safe_text` by default. `compose` uses a temporary local file while editing and deletes it after reading.

PromptGuard cannot protect prompts sent directly to an AI tool unless a pre-submit hook or wrapper is installed, enabled, trusted, and actually runs.

## Browser Extension: Live Prompt Protection

PromptGuard includes a browser extension prototype that scans prompt text locally while you type in supported browser text boxes. It shows risk warnings, detected categories, masked previews, and can anonymise the prompt before sending.

Load it as an unpacked Chrome, Edge, or Chromium extension:

1. Open `chrome://extensions` or `edge://extensions`.
2. Enable Developer Mode.
3. Click **Load unpacked**.
4. Select the `browser-extension` folder.
5. Open `browser-extension/demo/test_page.html` or a supported AI site.
6. Type a fake risky prompt.
7. Click **Anonymise Prompt** before sending.

The extension is best effort. Dynamic web apps can change DOM structure and send behavior. PromptGuard cannot guarantee every send path is intercepted. Use the Codex hook or local workflows for stronger pre-submit enforcement where available.

Run the extension engine tests:

```bash
npm --prefix browser-extension test
```

See `docs/browser_extension.md` for details.

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

## Codex Pre-Submit Protection

PromptGuard can protect Codex prompts only when it runs before submission. The Codex skill is useful guidance, but it is not a privacy boundary. The real pre-submit guardrail is the Codex `UserPromptSubmit` hook.

Install the repo-local hook:

```bash
promptguard install-codex-hook
```

Install the user-global hook for new Codex chats and repos on this machine:

```bash
promptguard install-codex-hook --scope user
```

Then in Codex, review and trust the hook if prompted, or run `/hooks`. The hook only works when Codex hooks are installed, enabled, trusted, and actually executed for the relevant config layer.

Test safely with a generated fake secret prompt:

```bash
python - <<'PY'
import subprocess

fake_key = "s" + "k-" + "proj-" + "FAKE1234567890abcdefghijklmnop"
prompt = "OPENAI_API_KEY=" + fake_key
result = subprocess.run(["promptguard", "scan", "--text", prompt], text=True, capture_output=True, check=False)
print(result.stdout.replace(fake_key, "[GENERATED_FAKE_SECRET_REDACTED]"))
print(result.stderr.replace(fake_key, "[GENERATED_FAKE_SECRET_REDACTED]"))
PY
```

Expected behavior: PromptGuard blocks the prompt before submission and shows a safe rewritten version containing `[SECRET_REMOVED]`.

PromptGuard cannot protect prompts typed directly into an AI tool if the hook is not installed, enabled, and trusted.

Example `.promptguard.yml` policy:

```yaml
block_on:
  - CRITICAL
  - HIGH
warn_on:
  - MEDIUM
confidential_terms:
  - Project Sundial
client_names:
  - Acme Retail
bypass:
  enabled: true
  allow_levels:
    - LOW
    - MEDIUM
    - HIGH
  require_confirmation_for:
    - HIGH
    - CRITICAL
  allow_critical_bypass: false
  audit_log: true
```

## One-Time Bypass

When the Codex hook blocks a prompt, it shows three actions:

1. Use the safe rewritten prompt.
2. Bypass once, if your local policy allows that risk level.
3. Edit `.promptguard.yml` if the policy itself should change.

Bypass is one-time only. A bypass request applies to the current prompt execution and does not change `block_on`, `warn_on`, or any other policy setting.

CRITICAL bypass is disabled by default because CRITICAL findings usually mean raw secrets, credential URLs, private keys, or similarly high-impact data. To allow it, the config must include `CRITICAL` in `bypass.allow_levels` and set `bypass.allow_critical_bypass: true`.

For HIGH or CRITICAL risk, the user must confirm by typing exactly `BYPASS`. The confirmation copy warns that the prompt may contain sensitive data.

If `bypass.audit_log` is enabled, PromptGuard appends local JSONL metadata to `.promptguard/audit.log`. The audit log stores timestamp, risk level, detected categories, action, SHA-256 prompt hash, and available hook context. It does not store raw prompts or secrets. `.promptguard/` is ignored by git.

## Hook Usage

Hook templates are included for Codex and Claude Code:

- `hooks/codex/hooks.example.json`
- `hooks/codex/promptguard_hook.py`
- `hooks/claude-code/hooks.example.json`
- `hooks/claude-code/promptguard_hook.py`

Exact hook schemas can change. Treat these files as local templates and adapt paths for your installed Codex or Claude Code version.

See `docs/codex_pre_submit_hook.md` for the production-oriented Codex hook details.

For a GitHub-ready Codex and Claude Code installation guide, see `docs/coding-agent-hooks.md`. For a reusable agent prompt that installs and verifies PromptGuard safely, see `prompts/install-promptguard-for-coding-agents.md`.

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
