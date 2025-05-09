"""Poll for bus arrival times."""

import asyncio
from asyncio import timeout
import collections
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import SUBENTRY_BUS_STOP_CODE
from .model.bus_arrival import BusArrival
from .sg_bus_arrivals_service import ApiError, SgBusArrivalsService

_LOGGER = logging.getLogger(__name__)

type SgBusArrivalsConfigEntry = ConfigEntry[SgBusArrivalsService]


class BusArrivalUpdateCoordinator(
    DataUpdateCoordinator[dict[str, dict[str, BusArrival]]]
):
    """Coordinator that polls for bus arrival times."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SgBusArrivalsConfigEntry,
        service: SgBusArrivalsService,
        scan_interval: int,
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Bus arrival times",
            config_entry=config_entry,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=scan_interval),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True,
        )
        self._service = service

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        bus_stop_codes: set[str] = set()
        for subentry in self.config_entry.subentries.values():
            bus_stop_codes.add(subentry.data[SUBENTRY_BUS_STOP_CODE])

        all_bus_arrivals: dict[str, dict[str, BusArrival]] = collections.defaultdict(
            dict
        )
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with timeout(10):
                responses = await asyncio.gather(
                    *[
                        self._service.get_bus_arrivals(bus_stop_code)
                        for bus_stop_code in bus_stop_codes
                    ]
                )
                for response in responses:
                    # Bus arrivals for a specific bus stop code.
                    bus_arrivals: list[BusArrival] = response

                    # Populate the data structure with bus arrivals.
                    for bus_arrival in bus_arrivals:
                        all_bus_arrivals[bus_arrival.bus_stop_code][
                            bus_arrival.service_no
                        ] = bus_arrival
                _LOGGER.debug("coordinator updated data")
                return all_bus_arrivals
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
