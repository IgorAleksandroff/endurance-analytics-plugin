#!/usr/bin/env bash
# Check that every generated text is current, validate the plugin and pack it for both directories.
# One folder (plugins/endurance) makes both packages; they differ only in the other platform's manifests:
#   dist/endurance-openai-<version>.zip  OpenAI plugin portal (its portal reads a stray Claude manifest and warns)
#   dist/endurance-claude-<version>.zip  claude.ai Customize > Plugins > Upload (the directory itself reads GitHub)
# Usage: scripts/build.sh [--allow-placeholder]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/plugins/endurance"

python3 -I "$ROOT/scripts/sync-listing.py" --check
python3 -I "$ROOT/scripts/validate-openai.py" "$@" "$PLUGIN"
if command -v claude >/dev/null; then
  claude plugin validate "$PLUGIN"
else
  echo "claude CLI not found: Claude-side validation skipped" >&2
fi

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
