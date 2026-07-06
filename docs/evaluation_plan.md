# Evaluation Plan

PromptGuard should be evaluated as a risk-reduction tool, not a complete privacy guarantee.

## Metrics

- Detection recall: percentage of labeled sensitive examples where expected categories are detected.
- False positive rate: percentage of harmless examples incorrectly classified above `LOW`.
- Critical miss rate: percentage of critical examples not classified as `CRITICAL`.
- Rewrite utility: whether the rewritten prompt still contains enough technical context for useful coding help.
- Risk reduction: whether raw sensitive values are removed or generalized in the rewritten prompt.

## Dataset

The MVP includes at least 40 risky examples in `examples/risky_prompts.jsonl`, covering secrets, env files, production logs, PII, database URLs, legal/business context, financial amounts, client names, health data, and mixed prompts.

## Acceptance Targets For MVP

- No misses for bundled critical secret examples.
- No critical classification for harmless code examples.
- Safe rewrites remove raw secrets and direct PII in bundled examples.
- Risk escalation works when PII appears with legal, finance, or health context.

## Review Process

1. Add examples with fake placeholder values only.
2. Define expected categories and risk level.
3. Run `promptguard test-examples`.
4. Add or update pytest coverage for detector or anonymizer changes.
5. Review false positives before widening patterns.

