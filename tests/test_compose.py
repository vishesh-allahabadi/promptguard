from __future__ import annotations

import shlex
import sys
from pathlib import Path

from promptguard.cli import main


def _fake_editor_command(tmp_path: Path, prompt: str) -> tuple[str, Path]:
    marker = tmp_path / "edited_path.txt"
    script = tmp_path / "fake_editor.py"
    script.write_text(
        """
from pathlib import Path
import sys

marker = Path(sys.argv[1])
target = Path(sys.argv[3])
target.write_text(sys.argv[2], encoding="utf-8")
marker.write_text(str(target), encoding="utf-8")
""",
        encoding="utf-8",
    )
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(script))} {shlex.quote(str(marker))} {shlex.quote(prompt)}"
    return command, marker


def test_compose_reads_temp_file_and_deletes_it(tmp_path: Path, capsys) -> None:
    command, marker = _fake_editor_command(tmp_path, "Email jane@example.com")
    code = main(["compose", "--editor", command])
    output = capsys.readouterr().out
    temp_file = Path(marker.read_text(encoding="utf-8"))
    assert code == 0
    assert "[EMAIL]" in output
    assert "jane@example.com" not in output
    assert not temp_file.exists()


def test_compose_copy_copies_safe_prompt(monkeypatch, tmp_path: Path, capsys) -> None:
    copied: list[str] = []
    monkeypatch.setattr("promptguard.workflows.copy_text", copied.append)
    command, _marker = _fake_editor_command(tmp_path, "Email jane@example.com")
    code = main(["compose", "--editor", command, "--copy"])
    capsys.readouterr()
    assert code == 0
    assert copied == ["Email [EMAIL]"]


def test_compose_output_writes_safe_prompt(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "safe_prompt.txt"
    command, _marker = _fake_editor_command(tmp_path, "Email jane@example.com")
    code = main(["compose", "--editor", command, "--output", str(output_path)])
    capsys.readouterr()
    assert code == 0
    assert output_path.read_text(encoding="utf-8") == "Email [EMAIL]"
