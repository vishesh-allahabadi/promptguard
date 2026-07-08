import json

from promptguard.cli import main


def _generated_key() -> str:
    return "s" + "k-" + "proj-" + "FAKE1234567890abcdefghijklmnop"


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


def test_install_codex_hook_user_scope_writes_codex_home_and_preserves_config(tmp_path, capsys) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    config = codex_home / "config.toml"
    config.write_text(
        """
model = "test-model"

[features]
hooks = false
js_repl = false
""".lstrip(),
        encoding="utf-8",
    )

    assert main(["install-codex-hook", "--scope", "user", "--codex-home", str(codex_home)]) == 0

    hooks_json = codex_home / "hooks.json"
    hook_script = codex_home / "hooks" / "promptguard_user_prompt_submit.py"
    assert hooks_json.exists()
    assert hook_script.exists()
    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    serialized = json.dumps(data)
    assert str(hook_script) in serialized
    updated_config = config.read_text(encoding="utf-8")
    assert 'model = "test-model"' in updated_config
    assert "hooks = true" in updated_config
    assert "js_repl = false" in updated_config
    assert list(codex_home.glob("config.toml.bak.*"))
    output = capsys.readouterr().out
    assert "Backups:" in output


def test_install_codex_hook_user_scope_preserves_existing_hooks_json(tmp_path) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    hooks_json = codex_home / "hooks.json"
    hooks_json.write_text(
        json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}]}}),
        encoding="utf-8",
    )

    assert main(["install-codex-hook", "--scope", "user", "--codex-home", str(codex_home)]) == 0

    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    serialized = json.dumps(data)
    assert "echo stop" in serialized
    assert "promptguard_user_prompt_submit.py" in serialized
    assert list(codex_home.glob("hooks.json.bak.*"))


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


def test_user_scope_doctor_and_check(tmp_path, monkeypatch, capsys) -> None:
    codex_home = tmp_path / "codex-home"
    assert main(["doctor", "--scope", "user", "--codex-home", str(codex_home)]) == 1
    capsys.readouterr()
    assert main(["install-codex-hook", "--scope", "user", "--codex-home", str(codex_home)]) == 0
    capsys.readouterr()
    assert main(["doctor", "--scope", "user", "--codex-home", str(codex_home)]) == 0
    assert "scope: user" in capsys.readouterr().out
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    assert main(["check"]) == 0
    assert "user_hook_files_present: True" in capsys.readouterr().out


def test_generated_fake_secret_scan_is_flagged(capsys) -> None:
    generated = _generated_key()
    assert main(["scan", "--text", "Here is a generated key: " + generated]) == 1
    output = capsys.readouterr().out
    assert "risk: CRITICAL" in output


def test_generated_fake_env_dump_is_flagged(capsys) -> None:
    generated = _generated_key()
    prompt = "\n".join(["DEBUG=true", "OPENAI_API_KEY=" + generated])
    assert main(["scan", "--text", prompt]) == 1
    output = capsys.readouterr().out
    assert "risk: CRITICAL" in output
