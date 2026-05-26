from __future__ import annotations

import aiohttp

from pi_weather_station.config import AppConfig
from pi_weather_station.reports.models import WeatherReport


class ApiClient:
    STATION_AUTH_PATH = "/auth/station-auth"
    REFRESH_PATH = "/auth/refresh"
    SUBMIT_REPORT_PATH = "/reports"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.base_url: str = config.default_api_base_url.rstrip("/")
        self.access_token: str | None = None
        self.refresh_token: str | None = None

    async def resolve_base_url(self) -> str:
        if not self.config.api_url_file:
            return self.base_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.config.api_url_file,
                    timeout=10,
                ) as response:
                    response.raise_for_status()

                    text = (await response.text()).strip()

                    if text:
                        self.base_url = text.rstrip("/")

        except Exception as exc:
            print(
                f"Could not resolve API URL: {exc}. "
                f"Using fallback {self.base_url}",
                flush=True,
            )

        return self.base_url

    async def authenticate(self) -> bool:
        url = f"{self.base_url}{self.STATION_AUTH_PATH}"

        payload = {
            "id": self.config.station_id,
            "secret": self.config.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()

                    data = await response.json()

                    token = (
                        data.get("token")
                        or data.get("accessToken")
                        or data.get("jwt")
                    )

                    if not token:
                        print(
                            "Station auth succeeded but no token returned",
                            flush=True,
                        )
                        return False

                    self.access_token = (
                        data.get("token")
                        or data.get("accessToken")
                        or data.get("jwt")
                    )

                    self.refresh_token = (
                        data.get("refreshToken")
                        or data.get("refresh")
                    )

                    print(
                        f"Authenticated station {self.config.station_id}",
                        flush=True,
                    )

                    return True

        except Exception as exc:
            print(f"Station authentication failed: {exc}", flush=True)
            return False
        
    async def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False

        url = f"{self.base_url}{self.REFRESH_PATH}"
        payload = {"token": self.refresh_token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status in {401, 403}:
                        return False

                    response.raise_for_status()
                    data = await response.json()

                    self.access_token = (
                        data.get("token")
                        or data.get("accessToken")
                        or data.get("jwt")
                    )

                    self.refresh_token = (
                        data.get("refreshToken")
                        or data.get("refresh")
                        or self.refresh_token
                    )

                    return self.access_token is not None

        except Exception as exc:
            print(f"Token refresh failed: {exc}", flush=True)
            return False

    async def _submit_report_once(self, report: WeatherReport) -> tuple[bool, bool]:
        if not self.access_token:
            return False, True

        url = f"{self.base_url}{self.SUBMIT_REPORT_PATH}"

        payload = {
            "stationId": report.station_id,
            "windDirection": report.data.wind_dir,
            "windSpeed": report.data.wind_spd,
            "windGust": report.data.wind_gst,
            "tempAmbient": report.data.temp_amb,
            "tempGround": report.data.temp_gnd,
            "pressure": report.data.pressure,
            "humidity": report.data.humidity,
            "rainfall": report.data.rainfall,
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in {401, 403}:
                        return False, True

                    response.raise_for_status()

                    print(f"Uploaded report for {report.station_id}", flush=True)
                    return True, False

        except Exception as exc:
            print(f"Report upload failed: {exc}", flush=True)
            return False, False
    
    async def submit_report(self, report: WeatherReport) -> bool:
        if not self.access_token:
            authenticated = await self.authenticate()
            if not authenticated:
                return False

        ok, unauthorized = await self._submit_report_once(report)

        if ok:
            return True

        if not unauthorized:
            return False

        print("Report upload unauthorized; attempting token refresh", flush=True)

        refreshed = await self.refresh_access_token()

        if not refreshed:
            print("Refresh failed; re-authenticating station", flush=True)
            refreshed = await self.authenticate()

        if not refreshed:
            return False

        ok, _ = await self._submit_report_once(report)
        return ok