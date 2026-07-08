from pathlib import Path

from promptguard.cli import main


def test_cli_scan_returns_nonzero_for_critical(capsys) -> None:
    code = main(["scan", "--text", "token=abc1234567890abcdef"])
    output = capsys.readouterr().out
    assert code == 1
    assert "risk: CRITICAL" in output
    assert "action: block" in output


def test_cli_scan_accepts_positional_prompt(capsys) -> None:
    key = "s" + "k-" + "proj-" + "FAKE1234567890abcdefghijklmnop"
    code = main(["scan", "Here is a generated key: " + key])
    output = capsys.readouterr().out
    assert code == 1
    assert "risk: CRITICAL" in output


def test_cli_anonymize_returns_safe_text(capsys) -> None:
    code = main(["anonymize", "--text", "Email jane@example.com about invoice $12,430"])
    output = capsys.readouterr().out
    assert code == 0
    assert "[EMAIL]" in output
    assert "around $12k" in output


def test_cli_check_file(tmp_path: Path, capsys) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Production database postgres://u:p@example.com/app failed", encoding="utf-8")
    code = main(["check", "--file", str(prompt)])
    output = capsys.readouterr().out
    assert code == 1
    assert "[DATABASE_URL_REMOVED]" in output


def test_cli_test_examples_passes(capsys) -> None:
    code = main(["test-examples"])
    output = capsys.readouterr().out
    assert code == 0
    assert "passed" in output
