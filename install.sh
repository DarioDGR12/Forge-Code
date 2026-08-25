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
  "$PYTHON" -m pip install --user -e .
else
  DEST="${FORGE_HOME:-$HOME/.local/share/forge-code}"
  if [[ ! -d "$DEST/.git" ]]; then
    git clone --depth 1 https://github.com/DarioDGR12/Forge-Code.git "$DEST"
  fi
  "$PYTHON" -m pip install --user -e "$DEST"
fi

echo
echo "Installed. Add ~/.local/bin to PATH if needed, then run: forge --help"
