# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from forge_code.retry import with_retry


def test_retries_then_succeeds() -> None:
    state = {"n": 0}

    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise RuntimeError("HTTP 429 rate limit")
        return "ok"

    sleeps: list[float] = []
    assert with_retry(flaky, attempts=4, backoff=0.01, sleeper=sleeps.append) == "ok"
    assert state["n"] == 3
    assert sleeps


def test_does_not_retry_logic_errors() -> None:
    def boom() -> None:
        raise RuntimeError("bad request HTTP 400")

    try:
        with_retry(boom, attempts=3, sleeper=lambda _: None)
    except RuntimeError as exc:
        assert "400" in str(exc)
    else:
        raise AssertionError("should have raised")
