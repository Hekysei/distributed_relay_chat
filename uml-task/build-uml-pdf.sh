#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUML_FILE="${1:-"$SCRIPT_DIR/class-diagram.puml"}"

if [[ ! -f "$PUML_FILE" ]]; then
  echo "PUML file not found: $PUML_FILE" >&2
  exit 1
fi

JAR_PATH="$SCRIPT_DIR/plantuml.jar"
PLANTUML_VERSION="${PLANTUML_VERSION:-1.2025.2}"
JAR_URL="https://github.com/plantuml/plantuml/releases/download/v${PLANTUML_VERSION}/plantuml-${PLANTUML_VERSION}.jar"
SVG_FILE="${PUML_FILE%.puml}.svg"
PDF_FILE="${PUML_FILE%.puml}.pdf"

if [[ ! -f "$JAR_PATH" ]]; then
  echo "Downloading PlantUML $PLANTUML_VERSION..."
  curl -fsSL "$JAR_URL" -o "$JAR_PATH"
fi

echo "Building SVG from: $PUML_FILE"
rm -f "$SVG_FILE"
java -jar "$JAR_PATH" -tsvg "$PUML_FILE"

if [[ ! -f "$SVG_FILE" ]]; then
  echo "SVG was not generated: $SVG_FILE" >&2
  exit 1
fi

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "rsvg-convert is required to produce PDF (install librsvg)." >&2
  exit 1
fi

echo "Converting SVG to PDF"
rsvg-convert -f pdf -o "$PDF_FILE" "$SVG_FILE"
echo "Done: $PDF_FILE"
