#!/usr/bin/env bash
# Wire ExoMind into Pi and/or Hermes Agent: MCP server + skill.
# Usage: scripts/install-agent.sh [--agent pi|hermes|all] [--notes-root PATH] [--exom PATH] [--force]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT="all"
NOTES_ROOT="${HOME}/Yasna-Memory"
EXOM_BIN="$(command -v exom || true)"
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --agent) AGENT="$2"; shift 2 ;;
    --notes-root) NOTES_ROOT="$2"; shift 2 ;;
    --exom) EXOM_BIN="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[ -n "$EXOM_BIN" ] || { echo "exom not found; run 'cargo install --path .' or pass --exom PATH" >&2; exit 1; }

wants() { [ "$AGENT" = all ] || [ "$AGENT" = "$1" ]; }

install_skill() { # $1 = skills dir
  local dest="$1/exomind"
  if [ -f "$dest/SKILL.md" ] && [ "$FORCE" -eq 0 ]; then
    echo "  skill exists: $dest/SKILL.md (use --force to overwrite)"
    return
  fi
  mkdir -p "$dest"
  cp "$ROOT_DIR/skills/exomind/SKILL.md" "$dest/SKILL.md"
  echo "  skill -> $dest/SKILL.md"
}

if wants pi; then
  echo "Pi:"
  python3 - "$EXOM_BIN" "$NOTES_ROOT" <<'PY'
import json, os, sys
exom, notes = sys.argv[1], sys.argv[2]
p = os.path.expanduser("~/.pi/agent/mcp.json")
cfg = {}
if os.path.exists(p):
    with open(p) as f:
        cfg = json.load(f)
cfg.setdefault("mcpServers", {})["exomind"] = {
    "command": exom,
    "args": ["mcp", "--notes-root", notes],
    "description": "ExoMind persistent memory: recall, capture, index, doctor.",
}
os.makedirs(os.path.dirname(p), exist_ok=True)
with open(p, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
print(f"  mcp -> {p}")
PY
  install_skill "$HOME/.pi/agent/skills"
fi

if wants hermes; then
  echo "Hermes:"
  if ! command -v hermes >/dev/null; then
    echo "  hermes CLI not found; skipping MCP registration"
  elif hermes mcp list 2>/dev/null | grep -q 'exomind' && [ "$FORCE" -eq 0 ]; then
    echo "  mcp already registered: exomind (use --force to re-register)"
  else
    # `hermes mcp add` prompts to enable discovered tools; answer yes.
    if printf 'y\n' | hermes mcp add exomind --command "$EXOM_BIN" --args mcp --notes-root "$NOTES_ROOT" >/dev/null 2>&1; then
      echo "  mcp -> ~/.hermes/config.yaml (exomind)"
    else
      echo "  WARNING: 'hermes mcp add exomind' failed; check 'hermes mcp add --help'" >&2
    fi
  fi
  install_skill "$HOME/.hermes/skills"
fi

echo "DONE agent=$AGENT notes_root=$NOTES_ROOT"
