# Install PromptGuard for Coding Agents

PromptGuard scans prompts locally before they are submitted to coding agents. It can block or rewrite prompts containing secrets, PII, production context, legal/financial/health context, and other configured sensitive terms.

PromptGuard does not guarantee privacy, security, or compliance. It only protects a workflow when the hook or local command is installed, enabled, trusted, and actually runs before the prompt leaves your machine.

## Support Matrix

| Agent | Scope | Hook event | Status |
| --- | --- | --- | --- |
| Codex CLI/App | user/global via `~/.codex`; repo/local via `.codex` | `UserPromptSubmit` | Supported by `promptguard install-codex-hook` if your installed Codex version supports hooks |
| Claude Code | manual settings adapter only | `UserPromptSubmit` or the equivalent prompt-submit lifecycle event for your installed Claude Code version | Partial/planned; this repo includes a template hook but does not include `promptguard install-claude-hook` |

## What Is Supported Today

Codex install support exists through:

```bash
promptguard install-codex-hook
promptguard install-codex-hook --scope user
promptguard doctor
promptguard doctor --scope user
promptguard check
```

Codex repo/local scope installs `.codex/hooks.json` and `.codex/hooks/promptguard_user_prompt_submit.py` in the current Git repo.

Codex user/global scope installs `hooks.json` and `hooks/promptguard_user_prompt_submit.py` under `~/.codex` or `CODEX_HOME`. If a user-scope `config.toml` exists and disables hooks with `hooks = false` or `codex_hooks = false`, the installer backs it up and enables hooks.

Claude Code support exists as templates only:

```text
hooks/claude-code/hooks.example.json
hooks/claude-code/promptguard_hook.py
skills/claude-code/promptguard/
```

There is no `promptguard install-claude-hook` command in this repo yet. Use the Claude Code template only if your installed Claude Code version supports configuring shell commands for prompt-submit lifecycle events.

## Install For Codex

From the PromptGuard repo root, install the package:

```bash
python -m pip install -e .
```

Install for the current repo only:

```bash
promptguard install-codex-hook --scope repo
promptguard doctor --scope repo
promptguard check
```

Install for your user-level Codex config:

```bash
promptguard install-codex-hook --scope user
promptguard doctor --scope user
promptguard check
```

Codex may ask you to trust the hook. If your Codex UI supports it, open `/hooks`, review the PromptGuard command, and trust or enable it there. The hook should block, warn, or rewrite before Codex receives sensitive prompts.

## Install For Claude Code

This repo does not currently implement a Claude Code installer command. Do not run `promptguard install-claude-hook`; it is not available.

If your installed Claude Code version supports prompt-submit hooks through settings, adapt the template files:

```text
hooks/claude-code/hooks.example.json
hooks/claude-code/promptguard_hook.py
```

General manual process:

1. Inspect your Claude Code settings folder and hook schema for the installed version.
2. Back up any settings file you will touch.
3. Copy or reference `hooks/claude-code/promptguard_hook.py`.
4. Configure the Claude Code prompt-submit lifecycle event to run the hook command.
5. Preserve unrelated settings and existing hooks.
6. Restart Claude Code if required.
7. Run the safe verification below.

Claude Code hook schemas can change. Treat the included `hooks.example.json` as an adapter template, not as guaranteed current product documentation.

## Safe Verification

Never test with real secrets, customer PII, production database URLs, Stripe keys, OpenAI keys, cookies, health data, legal documents, or real client records. Do not paste production env files into an agent.

Use generated fake values only:

```bash
python - <<'PY'
import subprocess

fake_key = "sk-" + "proj-" + "FAKE1234567890abcdefghijklmnop"
prompt = "Here is my fake API key: " + fake_key

result = subprocess.run(
["promptguard", "scan", prompt],
text=True,
capture_output=True,
)

print("returncode:", result.returncode)
print("stdout:")
print(result.stdout.replace(fake_key, "[GENERATED_FAKE_SECRET_REDACTED]"))
print("stderr:")
print(result.stderr.replace(fake_key, "[GENERATED_FAKE_SECRET_REDACTED]"))
PY
```

Expected result: the command returns non-zero for a critical generated fake secret and the printed output redacts the generated fake value.

For direct Codex hook invocation after repo-scope install:

```bash
python - <<'PY'
import json
import subprocess

fake_key = "sk-" + "proj-" + "FAKE1234567890abcdefghijklmnop"
event = {
    "hook_event_name": "UserPromptSubmit",
    "prompt": "Here is my fake API key: " + fake_key,
    "cwd": "/tmp",
    "session_id": "safe-test",
    "turn_id": "safe-test",
    "permission_mode": "default",
    "model": "safe-test",
}

result = subprocess.run(
    ["python", ".codex/hooks/promptguard_user_prompt_submit.py"],
    input=json.dumps(event),
    text=True,
    capture_output=True,
)

print("returncode:", result.returncode)
print("stdout:")
print(result.stdout.replace(fake_key, "[GENERATED_FAKE_SECRET_REDACTED]"))
print("stderr:")
print(result.stderr.replace(fake_key, "[GENERATED_FAKE_SECRET_REDACTED]"))
PY
```

Expected result: PromptGuard blocks, warns, or rewrites before the agent continues, depending on policy and hook event support.

## Fresh-Folder Verification

Use a clean folder to confirm user/global hooks are not only working in this repo:

```bash
mkdir -p /tmp/promptguard-agent-hook-test
cd /tmp/promptguard-agent-hook-test
promptguard check
```

Then open Codex or Claude Code from that folder. Submit a generated fake-secret test using the safe method above. The expected result is that PromptGuard blocks, warns, or rewrites before the agent continues.

Do not claim the install is complete unless either a fresh-session agent hook blocks/warns before submission or a direct hook invocation passes with generated fake values.

## Troubleshooting

### `promptguard` Not Found On PATH

Install PromptGuard in the Python environment used by your shell:

```bash
python -m pip install -e .
python -m pip show promptguard
```

If your agent runs hooks in a different shell, use an absolute Python path or reinstall in that environment.

### Hook File Exists But The Agent Does Not Block

Run:

```bash
promptguard doctor --scope repo
promptguard doctor --scope user
```

Then verify that the agent hook feature is enabled, the relevant config layer is loaded, and the hook command points to the expected file.

### Hook Needs Trust Approval

Codex may require manual review and trust before executing hooks. Open `/hooks` if your UI supports it, inspect the PromptGuard command, then approve it.

### Wrong Config Folder

For Codex user/global installs, check `CODEX_HOME` and `~/.codex`:

```bash
echo "$CODEX_HOME"
promptguard doctor --scope user
```

For Claude Code, inspect the settings folder and hook schema for your installed Claude Code version.

### Repo-Local Hook Works But Global Hook Does Not

Run:

```bash
promptguard install-codex-hook --scope user
promptguard doctor --scope user
promptguard check
```

Open the agent from a fresh folder and repeat the generated fake-secret verification.

### Shell Asks About Git Hooks Instead Of Agent Hooks

PromptGuard coding-agent hooks are not Git hooks. They are configured in Codex or Claude Code settings and should run on prompt-submit lifecycle events, not on `pre-commit`, `pre-push`, or other Git events.

### Claude Code Support Missing Or Not Installed

This repo currently provides a Claude Code hook template, not a supported installer. If your installed Claude Code version does not support prompt-submit shell hooks, use `promptguard safe`, `promptguard clip`, or `promptguard compose` as local workflows instead.

