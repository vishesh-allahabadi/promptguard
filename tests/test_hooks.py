import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOKS = (
    ROOT / "hooks" / "codex" / "promptguard_hook.py",
    ROOT / "hooks" / "claude-code" / "promptguard_hook.py",
)


def run_hook(hook: Path, prompt: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(hook)],
        input=prompt,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )


def test_hooks_block_critical_prompts() -> None:
    for hook in HOOKS:
        result = run_hook(hook, "OPENAI_API_KEY=sk-FAKEopenaiKey1234567890abcd")
        assert result.returncode != 0
        assert "PromptGuard blocked" in result.stderr
        assert "[SECRET_REMOVED]" in result.stderr


def test_hooks_allow_safe_prompts() -> None:
    for hook in HOOKS:
        result = run_hook(hook, "How do I refactor this harmless Python function?")
        assert result.returncode == 0
        assert "blocked" not in result.stderr


def test_hooks_warn_for_medium_or_high_prompts() -> None:
    for hook in HOOKS:
        result = run_hook(hook, "Email jane@example.com about invoice $12,430")
        assert result.returncode == 0
        assert "PromptGuard warning" in result.stderr
        assert "[EMAIL]" in result.stderr
        assert "around $12k" in result.stderr
