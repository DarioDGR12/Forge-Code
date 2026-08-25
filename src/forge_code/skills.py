# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path


def load_skills(root: Path, limit: int = 8) -> str:
    folder = root / ".forge" / "skills"
    if not folder.is_dir():
        return ""
    chunks: list[str] = []
    for path in sorted(folder.glob("*.md"))[:limit]:
        body = path.read_text(encoding="utf-8", errors="replace")[:4000]
        chunks.append(f"# skill:{path.stem}\n{body}")
    return "\n\n".join(chunks)
