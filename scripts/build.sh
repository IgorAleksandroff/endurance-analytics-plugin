#!/usr/bin/env bash
# Check that every generated text is current, validate the plugin and pack it for both directories.
# One folder (plugins/endurance) makes both packages; they differ only in the other platform's manifests:
#   dist/endurance-openai-<version>.zip  OpenAI plugin portal (its portal reads a stray Claude manifest and warns)
#   dist/endurance-claude-<version>.zip  claude.ai Customize > Plugins > Upload (the directory itself reads GitHub)
# Usage: [ENDURANCE_BACK=<backend checkout>] scripts/build.sh [--allow-placeholder]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/plugins/endurance"
EXPORT="${ENDURANCE_BACK:-$ROOT/../endurance-analytics-back}/docs/api/agent_surface.json"

cmp "$EXPORT" "$ROOT/agent-surface.json" || {
  echo "agent-surface.json differs from $EXPORT: run scripts/sync-listing.py --surface-from $EXPORT" >&2
  exit 1
}
python3 -I "$ROOT/scripts/sync-listing.py" --check
python3 -I "$ROOT/scripts/validate-openai.py" "$@" "$PLUGIN"
claude plugin validate "$PLUGIN"

VERSION="$(python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["version"])' "$ROOT/listing.json")"
mkdir -p "$ROOT/dist"

pack() { # pack <zip> <find exclusions...>
  local out="$ROOT/dist/$1"; shift
  rm -f "$out"
  (
    cd "$PLUGIN"
    find . -type f ! -name '.DS_Store' "$@" | sed 's|^\./||' | LC_ALL=C sort | zip -X -q "$out" -@
  )
  unzip -l "$out" | tail -1
  echo "Built $out"
}

pack "endurance-openai-$VERSION.zip" ! -path './.claude-plugin/*' ! -path './.mcp.json'
pack "endurance-claude-$VERSION.zip" ! -path './plugin.json' ! -path './mcp.json' ! -path './skills/*/agents/*'
