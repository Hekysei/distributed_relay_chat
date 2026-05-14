#!/usr/bin/env sh
# Сборка TUI-клиента в tui_client.exe для Windows.
#
# - В Git Bash / MSYS / Cygwin на Windows: локально через PyInstaller
#   (нужны: pip install -r requirements.txt -r requirements-build.txt).
# - На Linux / macOS: удалённая сборка через GitHub Actions
#   (нужны установленный и залогиненный gh, сеть, репозиторий на GitHub).
set -e
cd "$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"

case "$(uname -s 2>/dev/null)" in
MINGW* | MSYS* | CYGWIN*)
  if command -v python3 >/dev/null 2>&1; then
    exec python3 scripts/build_tui.py "$@"
  fi
  exec python scripts/build_tui.py "$@"
  ;;
esac

if ! command -v gh >/dev/null 2>&1; then
  echo "Локально .exe с Linux не собрать. Установите GitHub CLI и залогиньтесь:" >&2
  echo "  https://cli.github.com/  →  gh auth login" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Выполните: gh auth login" >&2
  exit 1
fi

before=$(gh run list --workflow=build-tui-windows.yml --limit 1 --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || true)

echo "Запуск workflow «Build TUI client (Windows)»..."
gh workflow run build-tui-windows.yml

i=0
while [ "$i" -lt 90 ]; do
  rid=$(gh run list --workflow=build-tui-windows.yml --limit 1 --json databaseId --jq '.[0].databaseId // empty')
  if [ -n "$rid" ] && [ "$rid" != "$before" ]; then
    gh run watch "$rid" --exit-status
    out=dist-windows-ci
    rm -rf "$out"
    mkdir -p "$out"
    gh run download "$rid" -n tui_client-windows -D "$out"
    echo "Готово: $out/tui_client.exe"
    exit 0
  fi
  i=$((i + 1))
  sleep 2
done

echo "Не появился новый запуск workflow за отведённое время. Проверьте Actions на GitHub." >&2
exit 1
