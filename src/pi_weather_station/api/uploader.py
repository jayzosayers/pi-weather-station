import asyncio

from pi_weather_station.api.api_client import ApiClient
from pi_weather_station.reports.upload_queue import UploadQueue


class ReportUploader:
    def __init__(
        self,
        api_client: ApiClient,
        upload_queue: UploadQueue,
        retry_delay_seconds: int = 30,
    ) -> None:
        self.api_client = api_client
        self.upload_queue = upload_queue
        self.retry_delay_seconds = retry_delay_seconds
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        await self.api_client.resolve_base_url()
        await self.api_client.authenticate()

        while not self._stop_event.is_set():
            report = await self.upload_queue.get_next()

            ok = await self.api_client.submit_report(report)

            if not ok:
                print(
                    f"Report upload failed/skipped for {report.station_id}; requeueing",
                    flush=True,
                )
                await asyncio.sleep(self.retry_delay_seconds)
                await self.upload_queue.enqueue(report)

    def stop(self) -> None:
        self._stop_event.set()