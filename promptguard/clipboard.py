from __future__ import annotations

import platform
import shutil
import subprocess


class PromptGuardClipboardError(RuntimeError):
    pass


def copy_text(text: str) -> None:
    system = platform.system().lower()
    if system == "darwin":
        _run_copy(["pbcopy"], text)
        return
    if system == "windows":
        _run_copy(["clip"], text)
        return

    for command in ("wl-copy", "xclip", "xsel"):
        if shutil.which(command):
            if command == "xclip":
                _run_copy([command, "-selection", "clipboard"], text)
            elif command == "xsel":
                _run_copy([command, "--clipboard", "--input"], text)
            else:
                _run_copy([command], text)
            return
    raise PromptGuardClipboardError(_unavailable_message())


def paste_text() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return _run_paste(["pbpaste"])
    if system == "windows":
        powershell = shutil.which("powershell") or shutil.which("powershell.exe")
        if powershell:
            return _run_paste([powershell, "-NoProfile", "-Command", "Get-Clipboard"])
        raise PromptGuardClipboardError(_unavailable_message())

    for command in ("wl-paste", "xclip", "xsel"):
        if shutil.which(command):
            if command == "xclip":
                return _run_paste([command, "-selection", "clipboard", "-out"])
            if command == "xsel":
                return _run_paste([command, "--clipboard", "--output"])
            return _run_paste([command])
    raise PromptGuardClipboardError(_unavailable_message())


def _run_copy(command: list[str], text: str) -> None:
    if shutil.which(command[0]) is None:
        raise PromptGuardClipboardError(_unavailable_message())
    result = subprocess.run(command, input=text, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PromptGuardClipboardError(f"Clipboard copy failed. {detail}".strip())


def _run_paste(command: list[str]) -> str:
    if shutil.which(command[0]) is None:
        raise PromptGuardClipboardError(_unavailable_message())
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PromptGuardClipboardError(f"Clipboard read failed. {detail}".strip())
    return result.stdout


def _unavailable_message() -> str:
    return (
        "Clipboard tools are unavailable. Install pbcopy/pbpaste, wl-clipboard, "
        "xclip, xsel, or use --output instead."
    )
