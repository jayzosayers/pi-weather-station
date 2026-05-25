import asyncio
from dataclasses import dataclass

import serial

from pi_weather_station.commands.command_bus import CommandBus
from pi_weather_station.commands.parser import parse_command_text
from pi_weather_station.comms.serial_discovery import SerialDevice


@dataclass(frozen=True)
class SerialRadioConfig:
    baud_rate: int = 115200


class SerialRadioListener:
    def __init__(
        self,
        device: SerialDevice,
        command_bus: CommandBus,
        config: SerialRadioConfig,
    ) -> None:
        self.device = device
        self.command_bus = command_bus
        self.config = config
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        print(f"Opening serial radio: {self.device.device}", flush=True)

        try:
            with serial.Serial(
                self.device.device,
                baudrate=self.config.baud_rate,
                timeout=1,
                write_timeout=1,
            ) as port:
                while not self._stop_event.is_set():
                    line = await asyncio.to_thread(port.readline)

                    if not line:
                        continue

                    text = line.decode("utf-8", errors="replace").strip()

                    if not text:
                        continue

                    print(
                        f"Serial message from {self.device.device}: {text}",
                        flush=True,
                    )

                    response_text = await self._handle_text(text)

                    if response_text:
                        await asyncio.to_thread(
                            port.write,
                            (response_text + "\n").encode("utf-8"),
                        )

        except Exception as exc:
            print(
                f"Serial listener failed for {self.device.device}: {exc}",
                flush=True,
            )

    def stop(self) -> None:
        self._stop_event.set()

    async def _handle_text(self, text: str) -> str:
        try:
            command = parse_command_text(
                text,
                source=f"serial:{self.device.device}",
            )
            response = await self.command_bus.dispatch(command)

            if response.data:
                return f"{response.message} {response.data}"

            return response.message

        except Exception as exc:
            return f"ERROR: {exc}"