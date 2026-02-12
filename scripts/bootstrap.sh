#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/4] Checking Python..."
python3 --version

echo "[2/4] Installing package (user mode)..."
python3 -m pip install --user -e .

echo "[3/4] Initializing skeleton..."
python3 src/exomind/cli.py init --path "$ROOT_DIR"

echo "[4/4] Running doctor..."
python3 src/exomind/cli.py doctor --notes-root "$ROOT_DIR" --graph "$ROOT_DIR/.neural/graph.json"

echo "BOOTSTRAP_OK"
