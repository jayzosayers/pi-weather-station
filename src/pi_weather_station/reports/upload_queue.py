import asyncio
from collections import deque

from pi_weather_station.reports.models import WeatherReport


class UploadQueue:
    def __init__(self, max_size: int = 512) -> None:
        self._queue: deque[WeatherReport] = deque()
        self._max_size = max_size
        self._event = asyncio.Event()
        self._lock = asyncio.Lock()
        self.dropped_count = 0

    async def enqueue(self, report: WeatherReport) -> None:
        async with self._lock:
            while len(self._queue) >= self._max_size:
                self._queue.popleft()
                self.dropped_count += 1

            self._queue.append(report)
            self._event.set()

    async def get_next(self) -> WeatherReport:
        while True:
            async with self._lock:
                if self._queue:
                    report = self._queue.popleft()

                    if not self._queue:
                        self._event.clear()

                    return report

            await self._event.wait()

    async def size(self) -> int:
        async with self._lock:
            return len(self._queue)