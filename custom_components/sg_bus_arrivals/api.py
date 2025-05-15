"""Handle API calls to LTA DataMall for querying bus arrivals."""

from datetime import UTC, datetime
import logging
import time
from typing import Any

import aiohttp

from . import const
from .models import BusArrival, BusStop, NextBus

_LOGGER = logging.getLogger(__name__)


# https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf
class SgBusArrivalsService:
    """Service for handling API calls."""

    def __init__(self, session: aiohttp.ClientSession, account_key: str) -> None:
        """Initialize with the given account key."""

        self._session = session
        self._account_key = account_key

    async def _get_request(self, endpoint: str) -> Any:
        """Invoke API."""

        async with self._session.get(
            const.API_BASE_URL + endpoint,
            headers={"AccountKey": self._account_key},
        ) as response:
            _LOGGER.debug(
                "Invoking api, endpoint: %s, status: %s", endpoint, response.status
            )
            if response.status == 200:
                return await response.json()

            if response.status == 401:
                raise ApiAuthenticationError

            raise ApiGeneralError(response.status)

    async def authenticate(self) -> None:
        """Verify the account key by making an API call."""

        # any random API call will work but this is the fastest and simplest
        # ApiAuthenticationError is thrown if authentication fails
        await self._get_request("/BusServices")

    async def get_bus_stop(self, bus_stop_code: str) -> BusStop:
        """Get bus stop information by bus stop code."""

        bus_stop: BusStop | None = None
        page: int = 0
        while bus_stop is None:
            page = page + 1

            response: Any = await self._get_request(f"/BusStops?page={page}")

            # no more results
            if response["value"] == []:
                return None

            # filter by bus stop code
            bus_stop = next(
                (
                    bus_stop
                    for bus_stop in response["value"]
                    if bus_stop["BusStopCode"] == bus_stop_code
                ),
                None,
            )

        return BusStop(
            bus_stop["BusStopCode"],
            bus_stop["RoadName"],
            bus_stop["Description"],
        )

    async def get_all_bus_services(self) -> dict[str, set[str]]:
        """Get bus services."""

        start: float = time.time()

        all_bus_services: dict[str, set[str]] = {}

        page: int = 0
        while True:
            page = page + 1
            response: Any = await self._get_request(f"/BusRoutes?page={page}")

            if response["value"] == []:
                end: float = time.time()
                seconds_elapsed: float = end - start
                _LOGGER.info(
                    "Get all bus services completed in %f seconds", seconds_elapsed
                )
                return all_bus_services

            for bus_route in response["value"]:
                bus_stop_code: str = bus_route["BusStopCode"]
                if bus_stop_code not in all_bus_services:
                    all_bus_services[bus_stop_code] = set()

                bus_services: set[str] = all_bus_services[bus_stop_code]
                bus_services.add(bus_route["ServiceNo"])

    async def get_bus_services(self, bus_stop_code: str) -> list[str]:
        """Get bus services."""

        all_bus_services: dict[str, set[str]] = await self.get_all_bus_services()
        return all_bus_services[bus_stop_code]

    async def get_bus_arrivals(self, bus_stop_code: str) -> list[BusArrival]:
        """Get bus arrivals."""

        response: Any = await self._get_request(
            f"/v3/BusArrival?BusStopCode={bus_stop_code}"
        )

        return [
            BusArrival(
                response["BusStopCode"],
                bus_arrival["ServiceNo"],
                [
                    NextBus(
                        self._compute_arrival_minutes(
                            bus_arrival[index]["EstimatedArrival"]
                        ),
                        bus_arrival[index]["Type"].lower(),
                        bus_arrival[index]["Feature"].lower(),
                        bus_arrival[index]["Load"].lower(),
                    )
                    for index in [
                        "NextBus",
                        "NextBus2",
                        "NextBus3",
                    ]  # api returns exactly 3 items
                ],
            )
            for bus_arrival in response["Services"]
        ]

    def _compute_arrival_minutes(self, arrival_str: str) -> int:
        """Compute arrival minutes."""

        if arrival_str == "":
            return None

        arrival_datetime: datetime = datetime.fromisoformat(arrival_str)
        now_utc: datetime = datetime.now(UTC)

        minutes: float = (arrival_datetime - now_utc).total_seconds() / 60

        # If the bus is already past, return 0
        if minutes < 0:
            return 0

        return int(minutes)  # rounded down


class ApiGeneralError(Exception):
    """Error to indicate api failed."""

    def __init__(self, http_status: int) -> None:
        """Initialize with the given status code."""
        super().__init__(f"LTA DataMall API call failed with status code {http_status}")
        self.http_status = http_status


class ApiAuthenticationError(Exception):
    """Error to indicate api authentication failed."""

    def __init__(self) -> None:
        """Initialize with the given status code."""
        super().__init__("Authentication failed. Please check your API account key.")
