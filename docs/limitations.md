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

## Operational Guidance

- Review safe rewrites before submitting them to an AI system.
- Replace raw secrets with placeholders before writing prompts.
- Keep raw secrets out of tests, examples, commits, logs, and issue reports.
- Use organization-approved security and compliance controls where required.

