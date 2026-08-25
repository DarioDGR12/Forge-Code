# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from forge_code.tools.fetch import _strip_html, fetch_url


def test_fetch_rejects_non_http(tmp_path: Path) -> None:
    assert fetch_url(tmp_path, {"url": "file:///etc/passwd"}).startswith("error:")
    assert fetch_url(tmp_path, {"url": "ftp://example.com/x"}).startswith("error:")
    assert fetch_url(tmp_path, {"url": "not-a-url"}).startswith("error:")


def test_fetch_rejects_private_hosts(tmp_path: Path) -> None:
    for url in (
        "http://localhost/secret",
        "https://127.0.0.1/",
        "http://192.168.1.10/docs",
        "http://10.0.0.2/x",
        "http://169.254.169.254/latest/meta-data",
    ):
        assert "not allowed" in fetch_url(tmp_path, {"url": url})


def test_strip_html() -> None:
    html = "<html><script>alert(1)</script><p>Hello <b>docs</b></p></html>"
    assert "Hello docs" == _strip_html(html)
    assert "alert" not in _strip_html(html)
