import asyncio
import json
from typing import Any

from pi_weather_station.commands.command_bus import CommandBus
from pi_weather_station.commands.parser import parse_command_text


class LocalCommandServer:
    def __init__(
        self,
        command_bus: CommandBus,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.command_bus = command_bus
        self.host = host
        self.port = port
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port,
        )

        print(
            f"Local command server listening on {self.host}:{self.port}",
            flush=True,
        )

        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            raw = await reader.readline()
            text = raw.decode("utf-8", errors="replace").strip()

            command = parse_command_text(text, source="local-cli")
            response = await self.command_bus.dispatch(command)

            payload: dict[str, Any] = {
                "ok": response.ok,
                "message": response.message,
                "data": response.data,
            }

            writer.write((json.dumps(payload) + "\n").encode("utf-8"))
            await writer.drain()

        except Exception as exc:
            payload = {
                "ok": False,
                "message": str(exc),
                "data": None,
            }
            writer.write((json.dumps(payload) + "\n").encode("utf-8"))
            await writer.drain()

        finally:
            writer.close()
            await writer.wait_closed()