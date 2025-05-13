"""Handle API calls to LTA DataMall for querying bus arrivals."""

from datetime import UTC, datetime
import logging
from typing import Any

import aiohttp

from . import const
from .models import BusArrival, BusStop

_LOGGER = logging.getLogger(__name__)


# https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf
class SgBusArrivalsService:
    """Service for handling API calls."""

    def __init__(self, session: aiohttp.ClientSession, account_key: str) -> None:
        """Initialize with the given account key."""

        self._session = session
        self._account_key = account_key
        self._is_authenticated = False

    async def _get_request(self, endpoint: str, page: int = 1) -> Any:
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

    async def authenticate(self) -> bool:
        """Verify the account key by making an API call."""

        if self._is_authenticated:
            return True

        await self._get_request("/BusServices")
        return True

    async def get_bus_stop(self, bus_stop_code: str) -> BusStop:
        """Get bus stop information by bus stop code."""

        response: Any = await self._get_request("/BusStops")
        bus_stop: dict[str, str] = next(
            (
                bus_stop
                for bus_stop in response["value"]
                if bus_stop["BusStopCode"] == bus_stop_code
            ),
            None,
        )

        if bus_stop is None:
            return None

        return BusStop(
            bus_stop["BusStopCode"],
            bus_stop["RoadName"],
            bus_stop["Description"],
        )

    async def get_bus_services(self, bus_stop_code: str) -> list[str]:
        """Get bus services."""

        response: Any = await self._get_request("/BusRoutes")

        return [
            bus_stop["ServiceNo"]
            for bus_stop in filter(
                lambda bus_stop: bus_stop["BusStopCode"] == bus_stop_code,
                response["value"],
            )
        ]

    async def get_bus_arrivals(self, bus_stop_code: str) -> list[BusArrival]:
        """Get bus arrivals."""

        response: Any = await self._get_request(
            f"/v3/BusArrival?BusStopCode={bus_stop_code}"
        )

        return [
            BusArrival(
                response["BusStopCode"],
                bus_arrival["ServiceNo"],
                self._compute_arrival_minutes(
                    bus_arrival["NextBus"]["EstimatedArrival"]
                ),
                self._compute_arrival_minutes(
                    bus_arrival["NextBus2"]["EstimatedArrival"]
                ),
                self._compute_arrival_minutes(
                    bus_arrival["NextBus3"]["EstimatedArrival"]
                ),
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
