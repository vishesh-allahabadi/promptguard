from __future__ import annotations

import subprocess

import pytest

from promptguard import clipboard
from promptguard.clipboard import PromptGuardClipboardError
from promptguard.cli import main


def test_copy_text_uses_pbcopy_on_macos(monkeypatch) -> None:
    calls: list[tuple[list[str], str]] = []
    monkeypatch.setattr(clipboard.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(clipboard.shutil, "which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, input=None, text=None, capture_output=None, check=None):
        calls.append((command, input))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(clipboard.subprocess, "run", fake_run)
    clipboard.copy_text("safe")
    assert calls == [(["pbcopy"], "safe")]


def test_paste_text_raises_friendly_error_when_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(clipboard.platform, "system", lambda: "Linux")
    monkeypatch.setattr(clipboard.shutil, "which", lambda command: None)
    with pytest.raises(PromptGuardClipboardError, match="Clipboard tools are unavailable"):
        clipboard.paste_text()


def test_clip_reads_and_replaces_clipboard(monkeypatch, capsys) -> None:
    copied: list[str] = []
    monkeypatch.setattr("promptguard.workflows.paste_text", lambda: "Email jane@example.com")
    monkeypatch.setattr("promptguard.workflows.copy_text", copied.append)
    code = main(["clip"])
    output = capsys.readouterr().out
    assert code == 0
    assert copied == ["Email [EMAIL]"]
    assert "Safe rewritten prompt copied to clipboard." in output
    assert "risk: HIGH" in output
    assert "jane@example.com" not in output


def test_clip_print_can_print_safe_prompt(monkeypatch, capsys) -> None:
    copied: list[str] = []
    monkeypatch.setattr("promptguard.workflows.paste_text", lambda: "Email jane@example.com")
    monkeypatch.setattr("promptguard.workflows.copy_text", copied.append)
    code = main(["clip", "--print"])
    output = capsys.readouterr().out
    assert code == 0
    assert "[EMAIL]" in output
    assert "jane@example.com" not in output


def test_clip_empty_clipboard_exits_nonzero(monkeypatch, capsys) -> None:
    monkeypatch.setattr("promptguard.workflows.paste_text", lambda: "")
    code = main(["clip"])
    captured = capsys.readouterr()
    assert code == 1
    assert "Clipboard is empty" in captured.err


def test_clip_unavailable_exits_nonzero(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "promptguard.workflows.paste_text",
        lambda: (_ for _ in ()).throw(PromptGuardClipboardError("Clipboard tools are unavailable.")),
    )
    code = main(["clip"])
    captured = capsys.readouterr()
    assert code == 1
    assert "Clipboard tools are unavailable" in captured.err
