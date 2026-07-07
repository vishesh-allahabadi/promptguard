# Security Policy

PromptGuard is early-stage local-first security and privacy tooling. It helps reduce sensitive-data exposure, but it does not guarantee detection of every secret or every sensitive value.

## Reporting Security Issues

Do not submit real secrets, customer data, production logs, private keys, or confidential business context in public issues, pull requests, screenshots, examples, or discussions.

When reporting a security issue:

- Use safe placeholders such as `[SECRET_REMOVED]`, `[EMAIL]`, or `[CUSTOMER_NAME]`.
- Include the detector category or behavior you expected.
- Include a minimal reproduction that does not contain real credentials.
- Describe whether the issue involves scanning, anonymization, CLI output, hooks, examples, or documentation.

For now, please contact the maintainer via GitHub profile or repository discussion with safe placeholders only.

## Prioritized Issues

Maintainers will prioritize reports involving:

- Raw prompt leakage.
- Incorrect storage of sensitive data.
- Bypasses for critical secret detection.
- Unsafe examples containing real credentials.

## Non-Guarantee

PromptGuard is deterministic and pattern/config based. It can miss secrets, overflag harmless text, and preserve context that is still sensitive. Review safe rewrites before submitting them to another system.

