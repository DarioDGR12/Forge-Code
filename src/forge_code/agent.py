# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from forge_code.compact import compact_messages, estimate_chars
from forge_code.config import AppConfig
from forge_code.models import Completion, Message
from forge_code.permissions import PermissionGate
from forge_code.prompts import system_prompt
from forge_code.providers.factory import complete as default_complete
from forge_code.qa.runner import QAReport, run_qa
from forge_code.tools.registry import ToolRegistry, default_registry
from forge_code.usage import Usage

OnEvent = Callable[[str, str], None]
CompleteFn = Callable[..., Completion]


@dataclass
class TurnResult:
    text: str
    qa: QAReport | None = None
    writes: list[str] = field(default_factory=list)
    steps: int = 0
    usage: Usage = field(default_factory=Usage)
    compacted: bool = False


class Agent:
    def __init__(
        self,
        root: Path,
        cfg: AppConfig,
        registry: ToolRegistry | None = None,
        max_steps: int | None = None,
        on_event: OnEvent | None = None,
        complete_fn: CompleteFn | None = None,
    ):
        self.root = root
        self.cfg = cfg
        gate = PermissionGate(root, cfg.permissions)
        self.registry = registry or default_registry(gate)
        if self.registry.gate is None:
            self.registry.gate = gate
        self.max_steps = max_steps or cfg.max_steps
        self.on_event = on_event or (lambda _kind, _msg: None)
        self.complete_fn = complete_fn or default_complete

    def run(self, history: list[Message], user_text: str) -> TurnResult:
        messages = list(history)
        if not messages or messages[0].role != "system":
            messages.insert(0, Message(role="system", content=system_prompt(self.root, self.cfg.mode)))
        else:
            messages[0] = Message(role="system", content=system_prompt(self.root, self.cfg.mode))
        compacted = False
        if estimate_chars(messages) > self.cfg.compact_after_chars:
            messages = compact_messages(messages)
            compacted = True
            self.on_event("compact", "conversation compacted")
        messages.append(Message(role="user", content=user_text))

        writes: list[str] = []
        last_text = ""
        qa: QAReport | None = None
        usage = Usage()
        tools = self.registry.schemas(self.cfg.mode)
        step = 0

        for step in range(self.max_steps):
            completion = self.complete_fn(self.cfg, messages, tools)
            usage = usage.add(completion.usage)
            assistant = completion.message
            messages.append(assistant)
            if assistant.content:
                last_text = assistant.content
                self.on_event("assistant", assistant.content)
            if not assistant.tool_calls:
                break
            for call in assistant.tool_calls:
                preview = _preview_args(call.name, call.arguments)
                self.on_event("tool", preview)
                result = self.registry.execute(
                    self.root, call.name, call.arguments, mode=self.cfg.mode
                )
                if call.name in {"write_file", "edit_file", "apply_patch"} and not result.startswith(
                    "error:"
                ):
                    writes.append(str(call.arguments.get("path") or call.name))
                messages.append(
                    Message(
                        role="tool",
                        content=result,
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )
                self.on_event("tool_result", result[:800])
            if writes and self.cfg.qa.auto:
                qa = run_qa(self.root, timeout=self.cfg.qa.timeout, extra=self.cfg.qa.extra)
                self.on_event("qa", qa.summary())
                if not qa.ok:
                    messages.append(
                        Message(
                            role="user",
                            content=(
                                "Integrated QA failed after your edits. Fix the failures.\n"
                                + qa.summary()
                            ),
                        )
                    )
                    writes = []
                    continue
            if step == self.max_steps - 1:
                last_text = last_text or "Stopped: max tool steps reached."
        else:
            last_text = last_text or "Stopped: max tool steps reached."

        history.clear()
        history.extend(messages)
        return TurnResult(
            text=last_text,
            qa=qa,
            writes=[item for item in writes if item],
            steps=step + 1,
            usage=usage,
            compacted=compacted,
        )


def _preview_args(name: str, arguments: dict) -> str:
    if name in {"write_file", "edit_file", "read_file"}:
        return f"{name} {arguments.get('path', '')}"
    if name == "bash":
        command = str(arguments.get("command") or "")
        return f"bash {command[:80]}"
    if name == "grep":
        return f"grep {arguments.get('pattern', '')}"
    if name == "apply_patch":
        return "apply_patch"
    return f"{name} {arguments}"
