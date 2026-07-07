import json

from promptguard.cli import main


def test_install_codex_hook_creates_files_and_is_idempotent(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["install-codex-hook"]) == 0
    assert main(["install-codex-hook"]) == 0
    hooks_json = tmp_path / ".codex" / "hooks.json"
    hook_script = tmp_path / ".codex" / "hooks" / "promptguard_user_prompt_submit.py"
    assert hooks_json.exists()
    assert hook_script.exists()
    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    prompt_hooks = data["hooks"]["UserPromptSubmit"]
    serialized = json.dumps(prompt_hooks)
    assert "promptguard_user_prompt_submit.py" in serialized
    assert serialized.count("promptguard_user_prompt_submit.py") == 1
    assert "UserPromptSubmit" in hooks_json.read_text(encoding="utf-8")
    assert "Codex may require you to review and trust this hook using /hooks" in capsys.readouterr().out


def test_install_codex_hook_preserves_existing_hooks(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    hooks_dir = tmp_path / ".codex"
    hooks_dir.mkdir()
    hooks_json = hooks_dir / "hooks.json"
    hooks_json.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {"hooks": [{"type": "command", "command": "echo existing"}]}
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    assert main(["install-codex-hook"]) == 0
    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    serialized = json.dumps(data)
    assert "echo existing" in serialized
    assert "promptguard_user_prompt_submit.py" in serialized


def test_doctor_exits_1_without_hook_and_0_after_install(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["doctor"]) == 1
    missing_output = capsys.readouterr().out
    assert "hook_files_present: False" in missing_output
    assert main(["install-codex-hook"]) == 0
    capsys.readouterr()
    assert main(["doctor"]) == 0
    installed_output = capsys.readouterr().out
    assert "hooks_json_exists: True" in installed_output
    assert "hook_script_exists: True" in installed_output
    assert "Codex may require you to review and trust this hook using /hooks before it runs." in installed_output

