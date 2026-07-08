from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_links_agent_hook_docs_and_prompt() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/coding-agent-hooks.md" in readme
    assert "prompts/install-promptguard-for-coding-agents.md" in readme


def test_agent_hook_docs_use_generated_fake_secret_fragments() -> None:
    docs = (ROOT / "docs" / "coding-agent-hooks.md").read_text(encoding="utf-8")
    prompt = (ROOT / "prompts" / "install-promptguard-for-coding-agents.md").read_text(encoding="utf-8")

    assert '"sk-" + "proj-"' in docs
    assert '"sk-" + "proj-"' in prompt
    assert "Do not run `promptguard install-claude-hook`" in docs
    full_fake_key = "s" + "k-proj-" + "FAKE1234567890abcdefghijklmnop"
    assert full_fake_key not in docs
    assert full_fake_key not in prompt
