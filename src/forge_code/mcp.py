# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any

from forge_code.tools.base import ToolSpec


@dataclass
class MCPServerConfig:
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


class MCPError(RuntimeError):
    pass


def encode_message(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def decode_stream(buffer: bytes) -> tuple[dict[str, Any] | None, bytes]:
    sep = b"\r\n\r\n"
    if sep not in buffer:
        return None, buffer
    header, rest = buffer.split(sep, 1)
    length = 0
    for line in header.decode("ascii", errors="replace").splitlines():
        if line.lower().startswith("content-length:"):
            length = int(line.split(":", 1)[1].strip())
    if len(rest) < length:
        return None, buffer
    body, leftover = rest[:length], rest[length:]
    return json.loads(body.decode("utf-8")), leftover


class MCPClient:
    """Minimal MCP stdio client (initialize + tools/list + tools/call)."""

    def __init__(self, name: str, cfg: MCPServerConfig):
        self.name = name
        self.cfg = cfg
        self._proc: subprocess.Popen[bytes] | None = None
        self._buf = b""
        self._next_id = 1
        self._tools: list[dict[str, Any]] = []

    def start(self) -> None:
        if self._proc is not None:
            return
        env = os.environ.copy()
        env.update(self.cfg.env)
        self._proc = subprocess.Popen(
            [self.cfg.command, *self.cfg.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "forge", "version": "0.9.0"}})
        self.notify("notifications/initialized", {})
        listed = self.request("tools/list", {})
        self._tools = list((listed or {}).get("tools") or [])

    def close(self) -> None:
        if self._proc is None:
            return
        self._proc.terminate()
        try:
            self._proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        self._proc = None

    def tool_specs(self) -> list[ToolSpec]:
        self.start()
        specs: list[ToolSpec] = []
        for raw in self._tools:
            tool_name = str(raw.get("name") or "tool")
            full = f"mcp_{self.name}_{tool_name}"
            schema = raw.get("inputSchema") or {"type": "object", "properties": {}}
            specs.append(
                ToolSpec(
                    name=full,
                    description=f"[mcp:{self.name}] {raw.get('description') or tool_name}",
                    parameters=schema if isinstance(schema, dict) else {"type": "object"},
                    fn=self._caller(tool_name),
                    writes=True,
                    runs_command=True,
                )
            )
        return specs

    def _caller(self, tool_name: str):
        def _call(_root, args: dict[str, Any]) -> str:
            result = self.request("tools/call", {"name": tool_name, "arguments": args})
            if not isinstance(result, dict):
                return str(result)
            if result.get("isError"):
                return f"error: {result}"
            content = result.get("content") or []
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(str(block.get("text") or ""))
            return "\n".join(texts) or json.dumps(result)

        return _call

    def request(self, method: str, params: dict[str, Any]) -> Any:
        ident = self._next_id
        self._next_id += 1
        self._write({"jsonrpc": "2.0", "id": ident, "method": method, "params": params})
        while True:
            message = self._read()
            if message.get("id") == ident:
                if "error" in message:
                    raise MCPError(str(message["error"]))
                return message.get("result")

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params})

    def _write(self, payload: dict[str, Any]) -> None:
        assert self._proc and self._proc.stdin
        self._proc.stdin.write(encode_message(payload))
        self._proc.stdin.flush()

    def _read(self) -> dict[str, Any]:
        assert self._proc and self._proc.stdout
        while True:
            message, self._buf = decode_stream(self._buf)
            if message is not None:
                return message
            chunk = self._proc.stdout.read(1)
            if not chunk:
                raise MCPError(f"MCP server {self.name} closed")
            self._buf += chunk


_CLIENTS: list[MCPClient] = []


def load_mcp_tools(servers: dict[str, MCPServerConfig]) -> list[ToolSpec]:
    close_mcp()
    specs: list[ToolSpec] = []
    for name, cfg in servers.items():
        if not cfg.command:
            continue
        try:
            client = MCPClient(name, cfg)
            specs.extend(client.tool_specs())
            _CLIENTS.append(client)
        except (OSError, MCPError):
            continue
    return specs


def close_mcp() -> None:
    while _CLIENTS:
        _CLIENTS.pop().close()


def describe_mcp(servers: dict[str, MCPServerConfig]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for name, cfg in servers.items():
        cmdline = " ".join([cfg.command, *cfg.args]).strip()
        rows.append((name, cmdline, "configured"))
    return rows
