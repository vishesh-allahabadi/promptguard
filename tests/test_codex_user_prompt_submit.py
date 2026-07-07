import json

from promptguard.codex_hook import main


def _event(prompt: str) -> str:
    return json.dumps(
        {
            "hook_event_name": "UserPromptSubmit",
            "prompt": prompt,
            "cwd": "/tmp/project",
            "session_id": "s1",
            "turn_id": "t1",
            "permission_mode": "default",
            "model": "test-model",
        }
    )


def test_low_prompt_allows_with_empty_stdout(capsys) -> None:
    code = main(_event("How do I refactor this harmless Python function?"))
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == ""


def test_critical_prompt_blocks_without_raw_secret(capsys) -> None:
    raw_key = "sk-FAKEopenaiKey1234567890abcd"
    code = main(_event(f"OPENAI_API_KEY={raw_key}"))
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["decision"] == "block"
    reason = payload["reason"]
    assert "PromptGuard blocked" in reason
    assert "CRITICAL" in reason
    assert "[SECRET_REMOVED]" in reason
    assert raw_key not in reason


def test_high_prompt_blocks_by_default_without_raw_pii(capsys) -> None:
    code = main(_event("Email jane@example.com about invoice $12,430"))
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["decision"] == "block"
    reason = payload["reason"]
    assert "HIGH" in reason
    assert "[EMAIL]" in reason
    assert "around $12k" in reason
    assert "jane@example.com" not in reason


def test_medium_prompt_warns(capsys) -> None:
    code = main(_event("Production checkout is throwing a generic TypeError."))
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    output = payload["hookSpecificOutput"]
    assert output["hookEventName"] == "UserPromptSubmit"
    assert "PromptGuard warning" in output["additionalContext"]
    assert "production_indicator" in output["additionalContext"]


def test_config_can_warn_on_high_without_printing_raw_prompt(tmp_path, monkeypatch, capsys) -> None:
    config = tmp_path / ".promptguard.yml"
    config.write_text(
        """
block_on:
  - CRITICAL
warn_on:
  - HIGH
  - MEDIUM
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("PROMPTGUARD_CONFIG", str(config))
    code = main(_event("Email jane@example.com about invoice $12,430"))
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert "decision" not in payload
    output = payload["hookSpecificOutput"]
    assert "PromptGuard warning" in output["additionalContext"]
    assert "jane@example.com" not in output["additionalContext"]
    assert "$12,430" not in output["additionalContext"]


def test_plain_text_fallback_blocks_without_raw_secret(capsys) -> None:
    raw_key = "sk-FAKEopenaiKey1234567890abcd"
    code = main(f"OPENAI_API_KEY={raw_key}")
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["decision"] == "block"
    assert "[SECRET_REMOVED]" in payload["reason"]
    assert raw_key not in payload["reason"]

