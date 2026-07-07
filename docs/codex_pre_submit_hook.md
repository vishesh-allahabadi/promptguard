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

From the repo root:

```bash
promptguard install-codex-hook
```

Codex may require you to review and trust the hook using `/hooks` before it runs.

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
```

You can also point the hook to a config file:

```bash
PROMPTGUARD_CONFIG=/path/to/config.yml
```

## Safe Test

Use fake values only:

```bash
echo '{"hook_event_name":"UserPromptSubmit","prompt":"OPENAI_API_KEY=sk-FAKEopenaiKey1234567890abcd","cwd":"/tmp","session_id":"s1","turn_id":"t1","permission_mode":"default","model":"test"}' | python .codex/hooks/promptguard_user_prompt_submit.py
```

Expected: JSON stdout with `decision: block`, a reason containing `[SECRET_REMOVED]`, and no raw fake key.

## Known Limitations

- This protects only workflows where the Codex hook is installed, enabled, trusted, and actually executed.
- It cannot protect prompts pasted directly into another AI tool.
- Codex hook schemas can change; verify behavior against your installed Codex version.
- Medium-risk prompts proceed unless your policy blocks them.
- PromptGuard helps reduce sensitive-data exposure but does not guarantee privacy, security, or compliance.
