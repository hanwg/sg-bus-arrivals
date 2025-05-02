"""Handle API calls to LTA DataMall for querying bus arrivals."""

import logging

import aiohttp

from homeassistant.core import HomeAssistant

from . import const

_LOGGER = logging.getLogger(__name__)


class SgBusArrivalsService:
    """Service for handling API calls."""

    def __init__(self, hass: HomeAssistant, apiAccountKey: str) -> None:
        """Initialize with the given account key."""

        self._apiKey = apiAccountKey
        self._isAuthenticated = False

    async def authenticate(self) -> bool:
        """Verify the account key by making an API call."""

        if self._isAuthenticated:
            return True

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                const.API_BASE_URL + "/BusServices",
                headers={"AccountKey": self._apiKey},
            ) as response,
        ):
            if response.status != 200:
                _LOGGER.warning("Failed to authenticate: %s", response)

            return response.status == 200
