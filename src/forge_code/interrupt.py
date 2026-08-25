# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


class CancelledError(RuntimeError):
    """Raised when the user hits Ctrl+C mid-run."""


class CancelFlag:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def check(self) -> None:
        if self.cancelled:
            raise CancelledError("interrupted")

    def reset(self) -> None:
        self.cancelled = False
