# PromptGuard

Use PromptGuard before handling prompts that include logs, env files, credentials, customer data, production incidents, contracts, financial context, health context, legal context, or private business context.

## Rules

- Run PromptGuard locally before analyzing sensitive prompt material.
- Never request raw secrets from the user.
- Ask the user to replace secrets with placeholders when exact values are not required.
- Prefer safe prompt rewriting before analysis.
- Explain when exact values are required and when approximate values are enough.
- Do not claim complete protection.
- Keep raw sensitive data out of generated files, commits, logs, examples, and tests.

## Suggested Commands

```bash
promptguard scan --file prompt.txt
promptguard anonymize --file prompt.txt
```

If PromptGuard reports `CRITICAL`, do not process the raw prompt. Use the safe rewrite or ask the user to provide a redacted version.

