#!/usr/bin/env bash
# Validate the plugin and pack it for the OpenAI plugin portal.
# Usage: scripts/build-openai-zip.sh [--allow-placeholder]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/plugins/endurance"

python3 -I "$ROOT/scripts/validate-openai.py" "$@" "$PLUGIN"

VERSION="$(python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["version"])' "$PLUGIN/plugin.json")"
OUT="$ROOT/dist/endurance-openai-$VERSION.zip"

mkdir -p "$ROOT/dist"
rm -f "$OUT"

# Claude Code files stay out: the portal would otherwise pick up the Claude manifest
# and warn about an undeclared .mcp.json.
(
  cd "$PLUGIN"
  find . -type f \
    ! -path './.claude-plugin/*' \
    ! -path './.mcp.json' \
    ! -name '.DS_Store' \
    ! -path './dist/*' \
    | sed 's|^\./||' | LC_ALL=C sort \
    | zip -X -q "$OUT" -@
)

unzip -l "$OUT"
echo "Built $OUT"
