#!/usr/bin/env sh
# Запуск на GitHub Actions сборки TUI для Linux и Windows, затем скачивание
# обоих артефактов в одну локальную директорию:
#   tui_client-linux, tui_client-windows.exe
#
# Нужны: gh, gh auth login; оба workflow должны быть в default branch на GitHub.
set -e
cd "$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"

out=dist-cross-ci
while [ "$#" -gt 0 ]; do
  case "$1" in
  -o | --out)
    [ -n "${2:-}" ] || {
      echo "Ожидался каталог после $1" >&2
      exit 1
    }
    out=$2
    shift 2
    ;;
  -h | --help)
    echo "Использование: $0 [-o|--out КАТАЛОГ]" >&2
    echo "  По умолчанию КАТАЛОГ: dist-cross-ci" >&2
    exit 0
    ;;
  *)
    echo "Неизвестный аргумент: $1 (справка: --help)" >&2
    exit 1
    ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "Нужен GitHub CLI: https://cli.github.com/" >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "Выполните: gh auth login" >&2
  exit 1
fi

for wf in build-tui-linux.yml build-tui-windows.yml; do
  if ! gh workflow view "$wf" >/dev/null 2>&1; then
    echo "Workflow $wf на GitHub в ветке по умолчанию не найден." >&2
    echo "Залейте и смержите в default branch файлы из .github/workflows/" >&2
    exit 1
  fi
done

_ref_args() {
  _git_ref=
  if _git_ref=$(git symbolic-ref -q --short HEAD 2>/dev/null); then
    printf '%s' "--ref $_git_ref"
  else
    printf '%s' ""
  fi
}

_dispatch_wait_download() {
  workflow=$1
  artifact=$2
  tmp=$3
  before=$(gh run list --workflow="$workflow" --limit 1 --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || true)
  ref_line=$(_ref_args)
  echo "Запуск workflow $workflow ..."
  if [ -n "$ref_line" ]; then
    # shellcheck disable=SC2086
    gh workflow run "$workflow" $ref_line
  else
    gh workflow run "$workflow"
  fi
  i=0
  while [ "$i" -lt 90 ]; do
    rid=$(gh run list --workflow="$workflow" --limit 1 --json databaseId --jq '.[0].databaseId // empty')
    if [ -n "$rid" ] && [ "$rid" != "$before" ]; then
      gh run watch "$rid" --exit-status
      rm -rf "$tmp"
      mkdir -p "$tmp"
      gh run download "$rid" -n "$artifact" -D "$tmp"
      return 0
    fi
    i=$((i + 1))
    sleep 2
  done
  echo "Таймаут ожидания $workflow" >&2
  return 1
}

tmp_linux=$(mktemp -d "${TMPDIR:-/tmp}/tui-ci-linux.XXXXXX")
tmp_win=$(mktemp -d "${TMPDIR:-/tmp}/tui-ci-win.XXXXXX")
trap 'rm -rf "$tmp_linux" "$tmp_win"' EXIT

_dispatch_wait_download build-tui-linux.yml tui_client-linux "$tmp_linux" || exit 1
_dispatch_wait_download build-tui-windows.yml tui_client-windows "$tmp_win" || exit 1

linux_src=$(find "$tmp_linux" -type f \( -path '*/tui_client' -o -name tui_client \) ! -name '*.exe' | head -n 1)
win_src=$(find "$tmp_win" -type f -name 'tui_client.exe' | head -n 1)
if [ -z "$linux_src" ] || [ ! -f "$linux_src" ]; then
  echo "В артефакте Linux не найден tui_client (см. $tmp_linux)." >&2
  exit 1
fi
if [ -z "$win_src" ] || [ ! -f "$win_src" ]; then
  echo "В артефакте Windows не найден tui_client.exe (см. $tmp_win)." >&2
  exit 1
fi

rm -rf "$out"
mkdir -p "$out"
cp -f "$linux_src" "$out/tui_client-linux"
cp -f "$win_src" "$out/tui_client-windows.exe"
chmod +x "$out/tui_client-linux" 2>/dev/null || true

echo "Готово: $out/tui_client-linux, $out/tui_client-windows.exe"
