# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

MAX_BYTES = 80_000


def fetch_url(_root: Path, args: dict[str, Any]) -> str:
    url = str(args.get("url") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "error: only http(s) URLs are allowed"
    if _blocked_host(parsed.hostname or ""):
        return "error: host is not allowed"
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "Forge-Code/0.4 (docs fetch)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(MAX_BYTES + 1)
            ctype = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return f"error: HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return f"error: {exc.reason}"
    if len(raw) > MAX_BYTES:
        raw = raw[:MAX_BYTES]
        truncated = True
    else:
        truncated = False
    text = raw.decode("utf-8", errors="replace")
    if "html" in ctype.lower() or text.lstrip().lower().startswith("<!doctype") or text.lstrip().startswith("<html"):
        text = _strip_html(text)
    if truncated:
        text += "\n... [truncated]"
    return text.strip() or "(empty)"


_PRIVATE_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
}


def _blocked_host(host: str) -> bool:
    host = host.strip("[]").lower()
    if not host or host in _PRIVATE_HOSTS or host.endswith(".localhost"):
        return True
    parts = host.split(".")
    if len(parts) == 4 and all(part.isdigit() for part in parts):
        nums = [int(part) for part in parts]
        if nums[0] in {10, 127}:
            return True
        if nums[0] == 192 and nums[1] == 168:
            return True
        if nums[0] == 172 and 16 <= nums[1] <= 31:
            return True
        if nums[0] == 169 and nums[1] == 254:
            return True
    return False


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
