"""Handle API calls to LTA DataMall for querying bus arrivals."""

from datetime import UTC, datetime
import logging
import time
from typing import Any

import aiohttp

from .models import BusArrival, BusStop, NextBus, TrainServiceAlert

_LOGGER = logging.getLogger(__name__)

API_BASE_URL: str = "https://datamall2.mytransport.sg/ltaodataservice"
MAX_PAGES: int = 100
BUS_ARRIVALS_COUNT: int = 3


# https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf
class SgBusArrivals:
    """LTA DataMall API client."""

    def __init__(self, session: aiohttp.ClientSession, account_key: str) -> None:
        """Initialize with the given account key."""

        self._session = session
        self._account_key = account_key

    async def _get_request(self, endpoint: str) -> Any:
        """Invoke the given API endpoint."""

        async with self._session.get(
            API_BASE_URL + endpoint,
            headers={"AccountKey": self._account_key},
        ) as response:
            if response.status == 200:
                json: Any = await response.json()
                _LOGGER.debug(
                    "Api invoked, endpoint: %s, status: %s", endpoint, response.status
                )
                return json

            text: str = await response.text()
            _LOGGER.warning(
                "Api failed, endpoint: %s, status: %s, response: %s",
                endpoint,
                response.status,
                text,
            )

            if response.status == 401:
                raise ApiAuthenticationError

            raise ApiGeneralError(endpoint, response.status)

    async def authenticate(self) -> None:
        """Verify the account key by making an API call."""

        # any random API call will work but this is the fastest and simplest
        # ApiAuthenticationError is thrown if authentication fails
        await self._get_request("/TrainServiceAlerts")

    async def get_bus_stop(self, bus_stop_code: str) -> BusStop:
        """Get bus stop information by bus stop code."""

        page: int = 0
        while page < MAX_PAGES:
            page = page + 1

            response: Any = await self._get_request(f"/BusStops?page={page}")

            # no more results
            if response["value"] == []:
                return None

            # filter by bus stop code
            bus_stop = next(
                (
                    BusStop(
                        bus_stop["BusStopCode"],
                        bus_stop["RoadName"],
                        bus_stop["Description"],
                    )
                    for bus_stop in response["value"]
                    if bus_stop["BusStopCode"] == bus_stop_code
                ),
                None,
            )

            if bus_stop:
                return bus_stop

        return None

    async def get_all_bus_services(self) -> dict[str, set[str]]:
        """Get all bus services for all bus stops.

        Returns a mapping of bus stop codes to the bus services.
        This is a slow API call.
        """

        start: float = time.time()

        all_bus_services: dict[str, set[str]] = {}

        page: int = 0
        while page < MAX_PAGES:
            page = page + 1
            response: Any = await self._get_request(f"/BusRoutes?page={page}")

            if response["value"] == []:
                break

            for bus_route in response["value"]:
                bus_stop_code: str = bus_route["BusStopCode"]
                if bus_stop_code not in all_bus_services:
                    all_bus_services[bus_stop_code] = set()

                bus_services: set[str] = all_bus_services[bus_stop_code]
                bus_services.add(bus_route["ServiceNo"])

        end: float = time.time()
        seconds_elapsed: float = end - start
        _LOGGER.info("Get all bus services completed in %f seconds", seconds_elapsed)
        return all_bus_services

    async def get_bus_services(self, bus_stop_code: str) -> list[str]:
        """Get bus services for the given bus stop."""

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
                        bus_arrival[index]["Feature"].lower()
                        if bus_arrival[index]["Feature"] != ""
                        else "none",
                        bus_arrival[index]["Load"].lower(),
                    )
                    if bus_arrival[index]["EstimatedArrival"] != ""
                    else NextBus(None, None, None, None)
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

        arrival_datetime: datetime = datetime.fromisoformat(arrival_str)
        now_utc: datetime = datetime.now(UTC)

        minutes: float = (arrival_datetime - now_utc).total_seconds() / 60

        # If the bus is already past, return 0
        if minutes < 0:
            return 0

        return int(minutes)  # rounded down

    def get_bus_types(self) -> list[str]:
        """Get bus types."""
        return ["sd", "dd", "bd"]

    def get_features(self) -> list[str]:
        """Get bus features."""
        return ["wab", "none"]

    def get_bus_loads(self) -> list[str]:
        """Get bus loads."""
        return ["sea", "sda", "lsd"]

    def get_train_statuses(self) -> list[str]:
        """Get train service statuses."""
        return ["normal", "disrupted"]

    def get_train_lines(self) -> list[str]:
        """Get train service lines."""
        return [
            "ccl",
            "cel",
            "cgl",
            "dtl",
            "ewl",
            "nel",
            "nsl",
            "pel",
            "pwl",
            "sel",
            "swl",
            "bpl",
        ]

    async def get_train_service_alerts(self) -> dict[str, TrainServiceAlert]:
        """Get train service alerts."""
        alerts: dict[str, list[str]] = {}

        response: Any = await self._get_request("/TrainServiceAlerts")
        value: dict[str, Any] = response["value"]
        all_messages: list[str] = value["Message"]

        train_lines: list[str] = self.get_train_lines()
        for train_line in train_lines:
            messages: list[str] = [
                message["Content"]
                for message in all_messages
                if train_line in message["Content"]
            ]
            alerts[train_line] = TrainServiceAlert(
                "disrupted" if messages else "normal", messages
            )

        return alerts


class ApiGeneralError(Exception):
    """Error to indicate api failed."""

    def __init__(self, endpoint: str, http_status: int) -> None:
        """Initialize with the given status code."""
        super().__init__(
            f"LTA DataMall API call failed. Endpoint: {endpoint}, Status: {http_status}"
        )
        self.http_status = http_status


class ApiAuthenticationError(Exception):
    """Error to indicate api authentication failed."""

    def __init__(self) -> None:
        """Initialize with the given status code."""
        super().__init__("Authentication failed. Please check your API account key.")
