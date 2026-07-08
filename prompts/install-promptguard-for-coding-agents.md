# Copy-Paste Prompt: Install PromptGuard For Coding Agents

Install PromptGuard as a global/user-level prompt scanning hook for this coding agent.

Requirements:

- Do not use, request, print, or store real secrets.
- Do not test with real customer PII, production database URLs, Stripe keys, OpenAI keys, cookies, health data, legal documents, or real client records.
- Inspect existing agent config first.
- Back up every config file before changing it.
- Preserve unrelated settings and existing hooks.
- Prefer user/global scope when supported.
- Install only hooks that are supported by the installed PromptGuard version and the installed coding agent version.
- If a hook is not supported, document it as pending or manual; do not claim it works.
- Use generated fake secret-like strings by concatenating safe fragments at runtime.
- Verify from the current repo and from a clean folder.
- Include any manual trust review steps required by the agent UI.
- Do not claim success unless the hook actually blocks/warns in a fresh agent session or direct hook invocation passes with generated fake values.

Steps:

1. Inspect the repo and installed CLI:

   ```bash
   promptguard --help
   promptguard install-codex-hook --help
   promptguard doctor --help
   promptguard check --help
   ```

2. Inspect existing user/global config without modifying it:

   ```bash
   echo "$CODEX_HOME"
   ls -la "${CODEX_HOME:-$HOME/.codex}" 2>/dev/null || true
   ```

   For Claude Code, inspect the installed version's settings location and hook documentation before changing anything.

3. Back up touched config files before editing. Preserve all unrelated settings and existing hooks.

4. Install the Codex user/global hook if supported:

   ```bash
   promptguard install-codex-hook --scope user
   promptguard doctor --scope user
   promptguard check
   ```

5. For Claude Code, install only if this PromptGuard checkout includes a supported installer or if the installed Claude Code version supports the template hook schema. If no supported installer exists, report Claude Code as pending/manual and do not modify Claude Code settings.

6. Run safe generated fake-secret validation:

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

7. Verify from a clean folder:

   ```bash
   mkdir -p /tmp/promptguard-agent-hook-test
   cd /tmp/promptguard-agent-hook-test
   promptguard check
   ```

   Open the coding agent from that folder and submit a generated fake-secret prompt using the same safe fragment-concatenation method. Confirm the hook blocks, warns, or rewrites before the agent continues.

8. Review manual trust steps:

   - In Codex, open `/hooks` if available and review/trust the PromptGuard command.
   - In Claude Code, review the configured lifecycle hook according to the installed version's settings UI or files.

Final report:

- Files inspected.
- Config files changed.
- Backup files created.
- Commands run.
- Test results.
- Whether Codex user/global install is active.
- Whether Claude Code support is installed, manual-only, or pending.
- Manual trust steps still required.
- Any verification that could not be completed.

