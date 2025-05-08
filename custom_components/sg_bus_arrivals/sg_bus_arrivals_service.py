"""Handle API calls to LTA DataMall for querying bus arrivals."""

from datetime import UTC, datetime
import logging
from typing import Any

import aiohttp

from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError

from . import const
from .model.bus_arrival import BusArrival
from .model.bus_stop import BusStop

_LOGGER = logging.getLogger(__name__)


# https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf
class SgBusArrivalsService:
    """Service for handling API calls."""

    def __init__(self, _account_key: str) -> None:
        """Initialize with the given account key."""

        self._account_key = _account_key
        self._is_authenticated = False

    async def __get_request(self, endpoint: str, page: int = 1) -> Any:
        """Invoke API."""

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                const.API_BASE_URL + endpoint,
                headers={"AccountKey": self._account_key},
            ) as response,
        ):
            _LOGGER.debug(
                "Invoking api, endpoint: %s, status: %s", endpoint, response.status
            )
            if response.status == 200:
                return await response.json()

            if response.status == 401:
                raise ConfigEntryAuthFailed

            raise ApiError(response.status)

    async def authenticate(self) -> bool:
        """Verify the account key by making an API call."""

        if self._is_authenticated:
            return True

        await self.__get_request("/BusServices")
        return True

    async def get_bus_stop(self, bus_stop_code: str) -> BusStop:
        """Get bus stop information by bus stop code."""

        response = await self.__get_request("/BusStops")
        bus_stop = next(
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

        response = await self.__get_request("/BusRoutes")

        return [
            bus_stop["ServiceNo"]
            for bus_stop in filter(
                lambda bus_stop: bus_stop["BusStopCode"] == bus_stop_code,
                response["value"],
            )
        ]

    async def get_bus_arrivals(self, bus_stop_code: str) -> list[BusArrival]:
        """Get bus arrivals."""

        response = await self.__get_request(
            f"/v3/BusArrival?BusStopCode={bus_stop_code}"
        )

        return [
            BusArrival(
                response["BusStopCode"],
                bus_arrival["ServiceNo"],
                await self.__compute_arrival_minutes(
                    bus_arrival["NextBus"]["EstimatedArrival"]
                ),
                await self.__compute_arrival_minutes(
                    bus_arrival["NextBus2"]["EstimatedArrival"]
                ),
                await self.__compute_arrival_minutes(
                    bus_arrival["NextBus3"]["EstimatedArrival"]
                ),
            )
            for bus_arrival in response["Services"]
        ]

    async def __compute_arrival_minutes(self, arrival_str: str) -> int:
        """Compute arrival minutes."""

        if arrival_str == "":
            return None

        arrival_datetime = datetime.fromisoformat(arrival_str)
        now_utc = datetime.now(UTC)

        minutes = (arrival_datetime - now_utc).total_seconds() / 60
        return int(minutes)  # rounded down


class ApiError(HomeAssistantError):
    """Error to indicate api failed."""

    def __init__(self, status: int) -> None:
        """Initialize with the given status code."""
        super().__init__(f"LTA DataMall API call failed with status code {status}")
        self.status = status
