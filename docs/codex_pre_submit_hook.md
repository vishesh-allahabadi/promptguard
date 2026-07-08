# Codex Pre-Submit Hook

PromptGuard helps reduce sensitive-data exposure before a prompt reaches Codex by using a local `UserPromptSubmit` hook.

## Problem

A Codex skill can remind an agent to be careful, but it runs after the user has already sent text to Codex. If the prompt contains secrets, customer data, private business context, or production logs, that is too late for a privacy guardrail.

The `UserPromptSubmit` hook is intended to run before submission. PromptGuard scans locally, blocks high-risk prompts by policy, and returns a safe rewritten version for the user to submit instead.

## How It Works

Codex sends a JSON object on stdin to the hook. PromptGuard reads `prompt`, scans and anonymizes it locally, then returns one of:

- no stdout for allowed `LOW` risk prompts
- `hookSpecificOutput.additionalContext` for warnings
- `{"decision": "block", "reason": "..."}` for blocked prompts

PromptGuard does not store raw prompts permanently, does not call external APIs, and does not add telemetry.

## Install

From the repo root, install for the current repo:

```bash
promptguard install-codex-hook
```

For all new Codex chats and repos on the machine, install at user scope:

```bash
promptguard install-codex-hook --scope user
```

Codex may require you to review and trust the hook using `/hooks` before it runs. User-scope hooks are loaded from `~/.codex` and remain independent of project trust.

## Manual Install

Create `.codex/hooks/promptguard_user_prompt_submit.py` and `.codex/hooks.json`.

Example `.codex/hooks.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/env python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/promptguard_user_prompt_submit.py\"",
            "statusMessage": "PromptGuard is checking prompt privacy"
          }
        ]
      }
    ]
  }
}
```

## Policy

Default hook policy:

- block `CRITICAL`
- block `HIGH`
- warn `MEDIUM`
- allow `LOW`

Customize with `.promptguard.yml`:

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

Blocked prompts show clear actions: use the safe rewritten prompt, bypass once if local policy permits the detected risk level, or edit `.promptguard.yml` if the policy should change.

Bypass is scoped to the current hook invocation. It does not persist and does not modify policy settings.

CRITICAL bypass is disabled by default because CRITICAL findings commonly include raw credentials, private keys, database URLs, or other data that should not be casually sent to an AI tool. To allow CRITICAL bypass, set `allow_critical_bypass: true` and include `CRITICAL` in `bypass.allow_levels`.

HIGH and CRITICAL bypass require the confirmation phrase `BYPASS`. The confirmation prompt should make clear that the prompt may contain sensitive data.

When `bypass.audit_log` is enabled, PromptGuard writes local metadata to `.promptguard/audit.log`: timestamp, risk level, detected categories, action, SHA-256 prompt hash, and available hook context. It does not log raw prompts or secrets.

You can also point the hook to a config file:

```bash
PROMPTGUARD_CONFIG=/path/to/config.yml
```

## Safe Test

Use generated fake values only:

```bash
python - <<'PY'
import json
import subprocess

fake_key = "s" + "k-" + "proj-" + "FAKE1234567890abcdefghijklmnop"
event = {
    "hook_event_name": "UserPromptSubmit",
    "prompt": "OPENAI_API_KEY=" + fake_key,
    "cwd": "/tmp",
    "session_id": "s1",
    "turn_id": "t1",
    "permission_mode": "default",
    "model": "test",
}

result = subprocess.run(
    ["python", ".codex/hooks/promptguard_user_prompt_submit.py"],
    input=json.dumps(event),
    text=True,
    capture_output=True,
    check=False,
)
print(result.stdout.replace(fake_key, "[GENERATED_FAKE_SECRET_REDACTED]"))
print(result.stderr.replace(fake_key, "[GENERATED_FAKE_SECRET_REDACTED]"))
PY
```

Expected: JSON stdout with `decision: block`, a reason containing `[SECRET_REMOVED]`, and no raw fake key.

## Known Limitations

- This protects only workflows where the Codex hook is installed, enabled, trusted, and actually executed.
- It cannot protect prompts pasted directly into another AI tool.
- Codex hook schemas can change; verify behavior against your installed Codex version.
- Medium-risk prompts proceed unless your policy blocks them.
- PromptGuard helps reduce sensitive-data exposure but does not guarantee privacy, security, or compliance.
