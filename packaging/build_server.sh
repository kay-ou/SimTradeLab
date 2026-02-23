#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/ui/resources/server"

mkdir -p "$OUTPUT_DIR"
cd "$REPO_ROOT"
poetry install --with dev --extras server --quiet
poetry run pyinstaller packaging/server.spec --distpath "$OUTPUT_DIR" --workpath /tmp/pyinstaller-work --clean

echo "Built: $OUTPUT_DIR/simtradelab-server"
