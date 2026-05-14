#!/usr/bin/env python3
"""Сборка TUI-клиента через PyInstaller.

Запускайте на той же ОС, под которую нужен бинарник (PyInstaller не
кросс-компилирует Linux→Windows и т.п.).

  Linux / macOS:  python3 scripts/build_tui.py
  Windows:        python scripts\\build_tui.py

Перед сборкой: зависимости клиента и инструменты сборки.

  pip install -r requirements.txt -r requirements-build.txt

На Windows для curses нужен пакет windows-curses (уже в requirements.txt).
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "tui_client.py"


def _win_stdio_utf8() -> None:
    """Избегает UnicodeEncodeError (cp1252) при выводе кириллицы в консоль Windows / CI."""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        if not hasattr(stream, "reconfigure"):
            continue
        enc = getattr(stream, "encoding", None) or ""
        if enc.lower() in ("utf-8", "utf8"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, AttributeError):
            pass


def _have_pyinstaller() -> bool:
    try:
        import PyInstaller  # noqa: F401

        return True
    except ImportError:
        return False


def main() -> int:
    _win_stdio_utf8()
    parser = argparse.ArgumentParser(
        description="Собрать TUI-клиент (один исполняемый файл или папку).",
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="собрать каталог dist/tui_client/ вместо одного файла (--onefile)",
    )
    args = parser.parse_args()

    if not ENTRY.is_file():
        print(f"Не найден файл входа: {ENTRY}", file=sys.stderr)
        return 1

    if not _have_pyinstaller():
        print(
            "Не установлен PyInstaller. Выполните:\n"
            "  pip install -r requirements-build.txt",
            file=sys.stderr,
        )
        return 1

    cmd: list[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--name",
        "tui_client",
        str(ENTRY),
        "--paths",
        str(ROOT),
        "--collect-all",
        "websockets",
    ]
    if args.onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    print("Команда:", " ".join(cmd))
    try:
        subprocess.check_call(cmd, cwd=ROOT)
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller завершился с кодом {e.returncode}.", file=sys.stderr)
        return e.returncode or 1

    dist = ROOT / "dist"
    if args.onedir:
        sub = dist / "tui_client"
        exe = sub / ("tui_client.exe" if platform.system() == "Windows" else "tui_client")
        print(f"Готово: {exe}")
    else:
        name = "tui_client.exe" if platform.system() == "Windows" else "tui_client"
        print(f"Готово: {dist / name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
