from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass(frozen=True)
class Command:
    type: str
    payload: dict[str, Any]
    source: str = "internal"


@dataclass(frozen=True)
class CommandResponse:
    ok: bool
    message: str
    data: dict[str, Any] | None = None


CommandHandler = Callable[[Command], CommandResponse | Awaitable[CommandResponse]]


class CommandBus:
    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, command_type: str, handler: CommandHandler) -> None:
        self._handlers[command_type] = handler

    async def dispatch(self, command: Command) -> CommandResponse:
        handler = self._handlers.get(command.type)

        if handler is None:
            return CommandResponse(
                ok=False,
                message=f"Unknown command type: {command.type}",
            )

        result = handler(command)

        if inspect.isawaitable(result):
            return await result

        return result