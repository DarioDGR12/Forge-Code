# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

RETRYABLE = ("HTTP 429", "HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504", "timed out", "could not reach")


def with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    backoff: float = 0.8,
    sleeper: Callable[[float], None] = time.sleep,
) -> T:
    last: Exception | None = None
    for index in range(max(1, attempts)):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — classified below
            last = exc
            text = str(exc)
            if index >= attempts - 1 or not any(token in text for token in RETRYABLE):
                raise
            sleeper(backoff * (2**index))
    assert last is not None
    raise last
