"""Handle API calls to LTA DataMall for querying bus arrivals."""

import logging

import aiohttp

from homeassistant import exceptions
from homeassistant.core import HomeAssistant

from . import const
from .model.bus_stop import BusStop  # type: ignore  # noqa: PGH003

_LOGGER = logging.getLogger(__name__)


class SgBusArrivalsService:
    """Service for handling API calls."""

    def __init__(self, hass: HomeAssistant, _account_key: str) -> None:
        """Initialize with the given account key."""

        self._account_key = _account_key
        self._is_authenticated = False

    async def authenticate(self) -> bool:
        """Verify the account key by making an API call."""

        if self._is_authenticated:
            return True

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                const.API_BASE_URL + "/BusServices",
                headers={"AccountKey": self._account_key},
            ) as response,
        ):
            if response.status != 200:
                _LOGGER.warning("Failed to authenticate: %s", response)

            return response.status == 200

    async def get_bus_stop(self, bus_stop_code: str) -> BusStop:
        """Get bus stop information by bus stop code."""

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                const.API_BASE_URL + "/BusStops",
                headers={"AccountKey": self._account_key},
            ) as response,
        ):
            if response.status == 200:
                data = await response.json()
                bus_stop = next(
                    (
                        bus_stop
                        for bus_stop in data["value"]
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

            raise ApiError


class ApiError(exceptions.HomeAssistantError):
    """Error to indicate api failed."""
