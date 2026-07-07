# Safer Local Workflows

PromptGuard local workflows exist for the moments when a Codex hook is not the right interface. They let you write a prompt locally, scan it locally, rewrite it locally, and copy or save only the safe prompt before pasting it into an AI tool.

PromptGuard does not send prompts to an LLM, does not call external APIs, does not include telemetry, and does not keep a persistent raw prompt history.

## Recommended Workflow

1. Write the prompt locally.
2. Run `promptguard safe`, `promptguard clip`, or `promptguard compose`.
3. Review the safe rewritten prompt.
4. Paste or send only the safe prompt.

PromptGuard protects only when it runs before the prompt reaches the AI system.

## `promptguard safe`

Use `safe` when the prompt already exists as text, a file, or stdin.

```bash
promptguard safe --text "Production Stripe live key sk_live_FAKEstripeKey1234567890 failed for jane@example.com"
promptguard safe --file risky_prompt.txt --copy
cat risky_prompt.txt | promptguard safe --stdin
```

Useful options:

- `--copy` copies only the safe rewritten prompt.
- `--output safe_prompt.txt` writes only the safe rewritten prompt to a file.
- `--fail-on-block` exits non-zero when local policy blocks the prompt.
- `--config .promptguard.yml` uses explicit local policy and configured terms.

## `promptguard clip`

Use `clip` when you have already copied a risky prompt.

```bash
promptguard clip
promptguard clip --print
```

By default, `clip` reads the current clipboard, scans and rewrites the text locally, and replaces the clipboard with `safe_text`. It prints a risk summary and categories without printing the original clipboard content. `--print` prints the safe rewritten prompt.

Clipboard mode only protects when you explicitly run it. Clipboard contents may be visible to other local apps depending on your operating system and clipboard manager.

## `promptguard compose`

Use `compose` when you want to write the prompt in an editor before creating the safe version.

```bash
promptguard compose --copy
promptguard compose --editor "code --wait" --output safe_prompt.txt
```

PromptGuard opens a temporary local file in your editor, waits for the editor to close, reads the prompt, scans and rewrites it, then deletes the temporary file. Editors and operating systems may create backups, swap files, recent-file entries, or other local artifacts that PromptGuard does not control.

Editor selection order:

1. `--editor`
2. `$EDITOR`
3. `nano` on Unix when available
4. `notepad` on Windows

## Policy

Local workflows load policy from `--config` when provided. If no config path is provided, PromptGuard looks for `.promptguard.yml` in the current directory or parent directories up to the Git root.

Default local policy:

```yaml
block_on:
  - CRITICAL
  - HIGH
warn_on:
  - MEDIUM
```

When `--fail-on-block` is passed, `promptguard safe`, `promptguard clip`, and `promptguard compose` return a non-zero exit code if policy says `block`.

## Clipboard Limitations

PromptGuard uses OS clipboard tools instead of adding required dependencies:

- macOS: `pbcopy`, `pbpaste`
- Windows: `clip`, PowerShell `Get-Clipboard`
- Linux: `wl-copy`/`wl-paste`, `xclip`, or `xsel`

If none are available, PromptGuard exits with a friendly error. Use `--output` as a fallback.

## Privacy Notes

- `safe --copy` copies only `safe_text`, not the raw prompt.
- `clip` replaces the clipboard with `safe_text` by default.
- `compose` deletes its temporary file after reading it.
- PromptGuard does not make external calls.
- PromptGuard does not include telemetry or analytics.
- PromptGuard does not log raw prompts or keep persistent prompt history.

## Known Limitations

- Detection is deterministic and pattern/config based, so it can miss sensitive data or overflag harmless text.
- Safe rewrites may preserve context that is still sensitive.
- Clipboard contents may be exposed to other local applications.
- Compose mode cannot control third-party editor backups, swap files, or recent-file behavior.
- Local workflows do not automatically protect prompts typed directly into an AI tool.
