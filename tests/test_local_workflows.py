from __future__ import annotations

import io
import sys
from pathlib import Path

from promptguard.cli import main


CRITICAL_PROMPT = (
    "Production Stripe live key sk_live_FAKEstripeKey1234567890 failed "
    "for jane@example.com on invoice $12,430"
)


def test_safe_text_critical_prompt_outputs_safe_text(capsys) -> None:
    code = main(["safe", "--text", CRITICAL_PROMPT])
    output = capsys.readouterr().out
    assert code == 0
    assert "risk: CRITICAL" in output
    assert "policy: block" in output
    assert "[SECRET_REMOVED]" in output
    assert "[EMAIL]" in output
    assert "around $12k" in output
    assert "sk_live_FAKEstripeKey1234567890" not in output


def test_safe_text_harmless_prompt_is_low(capsys) -> None:
    prompt = "How do I refactor this harmless Python function?"
    code = main(["safe", "--text", prompt])
    output = capsys.readouterr().out
    assert code == 0
    assert "risk: LOW" in output
    assert "policy: allow" in output
    assert prompt in output


def test_safe_file_reads_prompt(tmp_path: Path, capsys) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text(CRITICAL_PROMPT, encoding="utf-8")
    code = main(["safe", "--file", str(prompt)])
    output = capsys.readouterr().out
    assert code == 0
    assert "[SECRET_REMOVED]" in output
    assert "sk_live_FAKEstripeKey1234567890" not in output


def test_safe_stdin_reads_prompt(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(CRITICAL_PROMPT))
    code = main(["safe", "--stdin"])
    output = capsys.readouterr().out
    assert code == 0
    assert "[SECRET_REMOVED]" in output
    assert "sk_live_FAKEstripeKey1234567890" not in output


def test_safe_output_writes_only_safe_text(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "safe_prompt.txt"
    code = main(["safe", "--text", CRITICAL_PROMPT, "--output", str(output_path)])
    capsys.readouterr()
    assert code == 0
    saved = output_path.read_text(encoding="utf-8")
    assert "[SECRET_REMOVED]" in saved
    assert "sk_live_FAKEstripeKey1234567890" not in saved
    assert not saved.startswith("risk:")


def test_safe_copy_copies_only_safe_text(monkeypatch, capsys) -> None:
    copied: list[str] = []
    monkeypatch.setattr("promptguard.workflows.copy_text", copied.append)
    code = main(["safe", "--text", CRITICAL_PROMPT, "--copy"])
    capsys.readouterr()
    assert code == 0
    assert copied == [
        "Production payment provider live key [SECRET_REMOVED] failed for [EMAIL] on invoice around $12k"
    ]
    assert "sk_live_FAKEstripeKey1234567890" not in copied[0]


def test_safe_fail_on_block_exits_nonzero() -> None:
    code = main(["safe", "--text", CRITICAL_PROMPT, "--fail-on-block"])
    assert code == 1


def test_safe_json_output_is_valid(capsys) -> None:
    code = main(["--json", "safe", "--text", "Email jane@example.com"])
    output = capsys.readouterr().out
    assert code == 0
    assert '"risk_level": "HIGH"' in output
    assert '"safe_text": "Email [EMAIL]"' in output


def test_policy_config_allows_high_with_fail_on_block(tmp_path: Path, capsys) -> None:
    config = tmp_path / ".promptguard.yml"
    config.write_text(
        """
block_on:
  - CRITICAL
warn_on:
  - HIGH
""",
        encoding="utf-8",
    )
    code = main(["--config", str(config), "safe", "--text", "Email jane@example.com", "--fail-on-block"])
    output = capsys.readouterr().out
    assert code == 0
    assert "policy: warn" in output


def test_default_policy_blocks_high_with_fail_on_block(capsys) -> None:
    code = main(["safe", "--text", "Email jane@example.com", "--fail-on-block"])
    output = capsys.readouterr().out
    assert code == 1
    assert "policy: block" in output
