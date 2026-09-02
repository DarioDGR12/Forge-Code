#!/usr/bin/env bash
# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "python3 is required (3.10+)" >&2
  exit 1
fi

if [[ -f pyproject.toml ]] && grep -q 'name = "forge-code"' pyproject.toml; then
  ROOT="$(pwd)"
else
  ROOT="${FORGE_HOME:-$HOME/.local/share/forge-code}"
  if [[ ! -d "$ROOT/.git" ]]; then
    git clone --depth 1 https://github.com/DarioDGR12/Forge-Code.git "$ROOT"
  fi
fi

if ! "$PYTHON" -m venv --help >/dev/null 2>&1; then
  echo "python3-venv is required. On Debian/Ubuntu/Pop!_OS:" >&2
  echo "  sudo apt install -y python3-venv python3-full" >&2
  exit 1
fi

VENV="$ROOT/.venv"
"$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install -U pip
"$VENV/bin/pip" install -e "$ROOT"

BIN="$VENV/bin/forge"
echo
echo "Installed. This CLI is: $BIN"
echo
echo "  source $VENV/bin/activate"
echo "  forge --version    # must print forge 0.19.0"
echo "  forge              # OPEN FORGE menu"
echo
echo "Without activate:  $BIN"
echo "Unambiguous:       $VENV/bin/python -m forge_code"
echo
echo "If forge --version is not forge 0.19.0 (forge vibe, marketplace,"
echo "unrecognized arguments: menu), another program named forge is on PATH."
echo "which forge  shows which one. Use the venv binary above."
