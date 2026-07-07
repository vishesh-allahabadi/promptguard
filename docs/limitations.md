# Limitations

PromptGuard helps reduce sensitive-data exposure but does not guarantee privacy, security, or compliance.

## Known Limitations

- Regex detection can miss unusual secret formats.
- Regex detection can flag harmless text.
- Local configs must be maintained by the user.
- Safe rewrites may still reveal sensitive context.
- Hook templates may require adaptation as Codex and Claude Code schemas change.
- The tool does not know whether a token is active.
- The tool does not scan prompts after they leave the local machine.
- PromptGuard only protects Codex prompts when the hook is installed, enabled, trusted, and actually executed.
- It cannot protect prompts sent outside the guarded workflow.
- Clipboard mode only protects when the user explicitly runs it.
- Clipboard contents may be visible to other local apps depending on OS behavior.
- Compose mode creates a temporary local file while editing and deletes it afterward, but OS or editor backups may exist depending on editor behavior.
- PromptGuard does not control third-party editor behavior.
- Medium-risk warnings may still allow the raw prompt to proceed unless policy blocks them.
- Live highlighting while typing is not part of Milestone 1.

## Operational Guidance

- Review safe rewrites before submitting them to an AI system.
- Replace raw secrets with placeholders before writing prompts.
- Keep raw secrets out of tests, examples, commits, logs, and issue reports.
- Use organization-approved security and compliance controls where required.
