# Copyright 2026 Forge-Code contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from forge_code.ask import confirm_bash
from forge_code.compact import compact_messages, estimate_chars
from forge_code.config import AppConfig
from forge_code.diagnostics import format_diagnostics, run_diagnostics
from forge_code.diffview import preview_writes
from forge_code.hooks import run_hook
from forge_code.interrupt import CancelFlag, CancelledError
from forge_code.mcp import load_mcp_tools
from forge_code.models import Completion, Message
from forge_code.permissions import PermissionGate
from forge_code.prompts import system_prompt
from forge_code.providers.factory import complete as default_complete
from forge_code.qa.runner import QAReport, run_qa
from forge_code.tools.registry import ToolRegistry, default_registry
from forge_code.undo import checkpoint, remember_write, undo_last
from forge_code.usage import Usage, budget_hit

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
    interrupted: bool = False
    budget_hit: bool = False


class Agent:
    def __init__(
        self,
        root: Path,
        cfg: AppConfig,
        registry: ToolRegistry | None = None,
        max_steps: int | None = None,
        on_event: OnEvent | None = None,
        complete_fn: CompleteFn | None = None,
        cancel: CancelFlag | None = None,
        ask=None,
        attach_mcp: bool = True,
        session_usage: Usage | None = None,
    ):
        self.root = root
        self.cfg = cfg
        gate = PermissionGate(root, cfg.permissions)
        self.registry = registry or default_registry(gate, ask=ask or confirm_bash)
        if self.registry.gate is None:
            self.registry.gate = gate
        if ask is not None:
            self.registry.ask = ask
        if attach_mcp:
            for spec in load_mcp_tools(cfg.mcp):
                self.registry.add(spec)
        self.max_steps = max_steps or cfg.max_steps
        self.on_event = on_event or (lambda _kind, _msg: None)
        self.complete_fn = complete_fn or default_complete
        self.cancel = cancel or CancelFlag()
        self.session_usage = session_usage or Usage()

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
        snapped = False
        hit_budget = False

        try:
            for step in range(self.max_steps):
                self.cancel.check()
                reason = budget_hit(
                    self.cfg.resolved_model(),
                    self.session_usage.add(usage),
                    self.cfg.budget.max_usd,
                    self.cfg.budget.max_tokens,
                )
                if reason:
                    last_text = last_text or f"Stopped: {reason}."
                    self.on_event("budget", reason)
                    hit_budget = True
                    break
                streamed: list[str] = []

                def on_delta(piece: str, bucket: list[str] = streamed) -> None:
                    bucket.append(piece)
                    self.on_event("stream", piece)

                completion = self._complete(messages, tools, on_delta)
                usage = usage.add(completion.usage)
                assistant = completion.message
                messages.append(assistant)
                if assistant.content:
                    last_text = assistant.content
                    if not streamed:
                        self.on_event("assistant", assistant.content)
                    else:
                        self.on_event("stream_end", "")
                if not assistant.tool_calls:
                    break
                for call in assistant.tool_calls:
                    self.cancel.check()
                    preview = _preview_args(call.name, call.arguments)
                    self.on_event("tool", preview)
                    if call.name in {"write_file", "edit_file", "apply_patch"}:
                        hook = run_hook(
                            self.root,
                            "pre_edit",
                            {"FORGE_PATH": str(call.arguments.get("path") or "")},
                        )
                        if hook.startswith("error:"):
                            result = hook
                            messages.append(
                                Message(
                                    role="tool",
                                    content=result,
                                    tool_call_id=call.id,
                                    name=call.name,
                                )
                            )
                            self.on_event("hook", hook)
                            continue
                        if not snapped:
                            checkpoint(self.root, note=user_text[:60])
                            snapped = True
                        self._remember(call.name, call.arguments)
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
                if writes:
                    diff = preview_writes(self.root, writes)
                    if diff:
                        self.on_event("diff", diff)
                    post = run_hook(self.root, "post_edit", {"FORGE_PATHS": " ".join(writes)})
                    if post:
                        self.on_event("hook", post)
                    diags = run_diagnostics(self.root, writes)
                    if diags:
                        report = format_diagnostics(diags)
                        self.on_event("lsp", report)
                        messages.append(
                            Message(
                                role="user",
                                content="Language diagnostics after your edits. Fix them if they are real.\n"
                                + report,
                            )
                        )
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
        except CancelledError:
            run_hook(self.root, "post_turn", {"FORGE_TASK": user_text[:200]})
            history.clear()
            history.extend(messages)
            return TurnResult(
                text=last_text or "Interrupted.",
                qa=qa,
                writes=[item for item in writes if item],
                steps=step + 1,
                usage=usage,
                compacted=compacted,
                interrupted=True,
                budget_hit=hit_budget,
            )

        run_hook(self.root, "post_turn", {"FORGE_TASK": user_text[:200]})
        history.clear()
        history.extend(messages)
        return TurnResult(
            text=last_text,
            qa=qa,
            writes=[item for item in writes if item],
            steps=step + 1,
            usage=usage,
            compacted=compacted,
            budget_hit=hit_budget,
        )

    def _complete(self, messages: list[Message], tools: list, on_delta) -> Completion:
        try:
            return self.complete_fn(
                self.cfg,
                messages,
                tools,
                on_delta=on_delta,
                cancel=self.cancel,
            )
        except TypeError:
            return self.complete_fn(self.cfg, messages, tools)

    def _remember(self, name: str, arguments: dict) -> None:
        rel = str(arguments.get("path") or "")
        if not rel or name == "apply_patch":
            return
        path = self.root / rel
        existed = path.is_file()
        previous = path.read_text(encoding="utf-8") if existed else None
        remember_write(self.root, rel, existed, previous)


def undo_turn(root: Path) -> str:
    return undo_last(root)


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
    if name == "git_commit":
        return f"git_commit {arguments.get('message', '')}"
    if name == "fetch_url":
        return f"fetch_url {arguments.get('url', '')}"
    if name == "explore":
        return f"explore {arguments.get('question', '')}"
    if name == "memory_write":
        return f"memory_write {arguments.get('note', '')}"[:80]
    if name == "memory_read":
        return "memory_read"
    return f"{name} {arguments}"
