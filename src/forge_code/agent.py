# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from forge_code.config import AppConfig
from forge_code.models import Message
from forge_code.prompts import system_prompt
from forge_code.models import Completion
from forge_code.providers.factory import complete as default_complete
from forge_code.qa.runner import QAReport, run_qa
from forge_code.tools.registry import ToolRegistry, default_registry

OnEvent = Callable[[str, str], None]
CompleteFn = Callable[..., Completion]


@dataclass
class TurnResult:
    text: str
    qa: QAReport | None = None
    writes: list[str] = field(default_factory=list)
    steps: int = 0


class Agent:
    def __init__(
        self,
        root: Path,
        cfg: AppConfig,
        registry: ToolRegistry | None = None,
        max_steps: int = 24,
        on_event: OnEvent | None = None,
        complete_fn: CompleteFn | None = None,
    ):
        self.root = root
        self.cfg = cfg
        self.registry = registry or default_registry()
        self.max_steps = max_steps
        self.on_event = on_event or (lambda _kind, _msg: None)
        self.complete_fn = complete_fn or default_complete

    def run(self, history: list[Message], user_text: str) -> TurnResult:
        messages = list(history)
        if not messages or messages[0].role != "system":
            messages.insert(0, Message(role="system", content=system_prompt(self.root, self.cfg.mode)))
        else:
            messages[0] = Message(role="system", content=system_prompt(self.root, self.cfg.mode))
        messages.append(Message(role="user", content=user_text))

        writes: list[str] = []
        last_text = ""
        qa: QAReport | None = None
        tools = self.registry.schemas(self.cfg.mode)

        for step in range(self.max_steps):
            completion = self.complete_fn(self.cfg, messages, tools)
            assistant = completion.message
            messages.append(assistant)
            if assistant.content:
                last_text = assistant.content
                self.on_event("assistant", assistant.content)
            if not assistant.tool_calls:
                break
            for call in assistant.tool_calls:
                self.on_event("tool", f"{call.name} {call.arguments}")
                result = self.registry.execute(
                    self.root, call.name, call.arguments, mode=self.cfg.mode
                )
                if call.name in {"write_file", "edit_file"} and not result.startswith("error:"):
                    writes.append(str(call.arguments.get("path") or ""))
                messages.append(
                    Message(
                        role="tool",
                        content=result,
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )
                self.on_event("tool_result", result[:500])
            if writes and self.cfg.qa.auto:
                qa = run_qa(self.root, timeout=self.cfg.qa.timeout)
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
        return TurnResult(text=last_text, qa=qa, writes=[w for w in writes if w], steps=step + 1)
