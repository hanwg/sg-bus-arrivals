"""Handle API calls to LTA DataMall for querying bus arrivals."""

import logging
from typing import Any

import aiohttp

from homeassistant import exceptions
from homeassistant.core import HomeAssistant

from . import const
from .model.bus_stop import BusStop

_LOGGER = logging.getLogger(__name__)


class SgBusArrivalsService:
    """Service for handling API calls."""

    def __init__(self, hass: HomeAssistant, _account_key: str) -> None:
        """Initialize with the given account key."""

        self._account_key = _account_key
        self._is_authenticated = False

    async def get_request(self, endpoint: str, page: int = 1) -> Any:
        """Invoke API."""

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                const.API_BASE_URL + endpoint,
                headers={"AccountKey": self._account_key},
            ) as response,
        ):
            _LOGGER.info(
                "Invoking api, endpoint: %s, status: %s", endpoint, response.status
            )
            if response.status == 200:
                return await response.json()

            raise ApiError(response.status)

    async def authenticate(self) -> bool:
        """Verify the account key by making an API call."""

        if self._is_authenticated:
            return True

        await self.get_request("/BusServices")
        return True

    async def get_bus_stop(self, bus_stop_code: str) -> BusStop:
        """Get bus stop information by bus stop code."""

        response = await self.get_request("/BusStops")
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

        response = await self.get_request("/BusRoutes")

        return [
            bus_stop["ServiceNo"]
            for bus_stop in filter(
                lambda bus_stop: bus_stop["BusStopCode"] == bus_stop_code,
                response["value"],
            )
        ]


class ApiError(exceptions.HomeAssistantError):
    """Error to indicate api failed."""

    def __init__(self, status: int) -> None:
        """Initialize with the given status code."""
        self.status = status
