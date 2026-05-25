from datetime import datetime, timezone

from pi_weather_station.commands.command_bus import Command, CommandResponse
from pi_weather_station.config import AppConfig


class CommandHandlers:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def status(self, command: Command) -> CommandResponse:
        return CommandResponse(
            ok=True,
            message="Station online",
            data={
                "stationId": self.config.station_id,
                "mode": self.config.mode,
                "source": command.source,
                "timeUtc": datetime.now(timezone.utc).isoformat(),
            },
        )

    def get_latest_report(self, command: Command) -> CommandResponse:
        return CommandResponse(
            ok=False,
            message="No weather report available yet",
            data={
                "stationId": self.config.station_id,
            },
        )