import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


StationMode = Literal["lightweight", "relay", "hybrid", "combined"]


@dataclass(frozen=True)
class AppConfig:
    station_id: str
    api_key: str
    repo_url: str
    api_url_file: str
    default_api_base_url: str
    mode: StationMode
    raw: dict[str, Any] = field(repr=False)


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    station = raw.get("station", {})
    mode = station.get("mode", "hybrid")

    if mode not in {"lightweight", "relay", "hybrid", "combined"}:
        raise ValueError(f"Invalid station mode: {mode}")

    return AppConfig(
        station_id=raw.get("stationId", "UNKNOWN"),
        api_key=raw.get("apiKey", ""),
        repo_url=raw.get("repoUrl", ""),
        api_url_file=raw.get("apiUrlFile", ""),
        default_api_base_url=raw.get("defaultApiBaseUrl", ""),
        mode=mode,
        raw=raw,
    )