import asyncio
import math
import statistics
from dataclasses import dataclass

from pi_weather_station.reports.models import WeatherData


@dataclass(frozen=True)
class MeasurementConfig:
    radius_cm: float = 9.0
    adjustment: float = 1.18
    pulses_per_rotation: int = 2
    rain_bucket_size_mm: float = 0.2794
    measurement_seconds: int = 60
    wind_window_seconds: int = 5


class WeatherMeasurement:
    def __init__(self, config: MeasurementConfig) -> None:
        self.config = config

        self._wind_pulse_count = 0
        self._rain_tip_count = 0
        self._counter_lock = asyncio.Lock()

    async def measure_once(self) -> WeatherData:
        await self._reset_wind_counter()
        await self._reset_rain_counter()

        wind_speeds: list[float] = []
        wind_directions: list[float] = []

        windows = self.config.measurement_seconds // self.config.wind_window_seconds

        for _ in range(windows):
            await self._reset_wind_counter()

            direction = await self.read_wind_direction()

            await asyncio.sleep(self.config.wind_window_seconds)

            pulse_count = await self._get_wind_pulse_count()
            speed = self.calculate_wind_speed(
                pulse_count,
                self.config.wind_window_seconds,
            )

            wind_directions.append(direction)
            wind_speeds.append(speed)

        temp_amb, pressure, humidity = await self.read_bme280()
        temp_gnd = await self.read_ground_temperature()
        rainfall = await self._read_and_reset_rainfall()

        return WeatherData(
            wind_dir=round(self.average_direction(wind_directions), 1),
            wind_spd=round(statistics.mean(wind_speeds), 2) if wind_speeds else 0.0,
            wind_gst=round(max(wind_speeds), 2) if wind_speeds else 0.0,
            temp_amb=round(temp_amb, 2),
            temp_gnd=round(temp_gnd, 2),
            pressure=round(pressure, 2),
            humidity=round(humidity, 2),
            rainfall=round(rainfall, 2),
        )

    def record_wind_pulse(self) -> None:
        self._wind_pulse_count += 1

    def record_rain_tip(self) -> None:
        self._rain_tip_count += 1

    def calculate_wind_speed(self, pulse_count: int, seconds: int) -> float:
        rotations = pulse_count / self.config.pulses_per_rotation
        circumference_cm = 2 * math.pi * self.config.radius_cm
        distance_m = (circumference_cm * rotations) / 100
        speed_mps = distance_m / seconds
        return speed_mps * self.config.adjustment

    @staticmethod
    def average_direction(directions: list[float]) -> float:
        if not directions:
            return 0.0

        sin_sum = sum(math.sin(math.radians(d)) for d in directions)
        cos_sum = sum(math.cos(math.radians(d)) for d in directions)

        if sin_sum == 0 and cos_sum == 0:
            return 0.0

        angle = math.degrees(math.atan2(sin_sum, cos_sum))
        return angle % 360

    async def read_wind_direction(self) -> float:
        # TODO: replace with ADC wind vane read.
        return 270.0

    async def read_bme280(self) -> tuple[float, float, float]:
        # TODO: replace with real BME280 read.
        # Returns temp_amb, pressure, humidity.
        return 18.5, 1012.3, 74.0

    async def read_ground_temperature(self) -> float:
        # TODO: replace with real DS18B20 read.
        return 15.2

    async def _read_and_reset_rainfall(self) -> float:
        async with self._counter_lock:
            tips = self._rain_tip_count
            self._rain_tip_count = 0

        return tips * self.config.rain_bucket_size_mm

    async def _reset_wind_counter(self) -> None:
        async with self._counter_lock:
            self._wind_pulse_count = 0

    async def _reset_rain_counter(self) -> None:
        async with self._counter_lock:
            self._rain_tip_count = 0

    async def _get_wind_pulse_count(self) -> int:
        async with self._counter_lock:
            return self._wind_pulse_count