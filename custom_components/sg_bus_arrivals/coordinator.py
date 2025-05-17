"""Poll for bus arrival times."""

from __future__ import annotations

import asyncio
from asyncio import Task, timeout
import collections
from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiAuthenticationError, ApiGeneralError, SgBusArrivals
from .const import SUBENTRY_CONF_BUS_STOP_CODE, SUBENTRY_TYPE_BUS_SERVICE
from .models import BusArrival, TrainServiceAlert

_LOGGER = logging.getLogger(__name__)


@dataclass
class SgBusArrivalsData:
    """SgBusArrivals data class."""

    api: SgBusArrivals
    bus_arrivals_coordinator: BusArrivalsUpdateCoordinator
    train_service_alerts_coordinator: TrainServiceAlertsUpdateCoordinator


type SgBusArrivalsConfigEntry = ConfigEntry[SgBusArrivalsData]


class TrainServiceAlertsUpdateCoordinator(
    DataUpdateCoordinator[dict[str, TrainServiceAlert]]
):
    """Coordinator that polls for train service alerts."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SgBusArrivalsConfigEntry,
        sg_bus_arrivals: SgBusArrivals,
        scan_interval: int,
    ) -> None:
        """Initialize the train service alerts coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Train service alerts",
            config_entry=config_entry,
            update_interval=timedelta(seconds=scan_interval),
            always_update=True,
        )
        self._sg_bus_arrivals = sg_bus_arrivals

    async def _async_update_data(self):
        """Fetch train service alerts from api."""
        return await self._sg_bus_arrivals.get_train_service_alerts()


class BusArrivalsUpdateCoordinator(
    DataUpdateCoordinator[dict[str, dict[str, BusArrival]]]
):
    """Coordinator that polls for bus arrival times."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SgBusArrivalsConfigEntry,
        sg_bus_arrivals: SgBusArrivals,
        scan_interval: int,
    ) -> None:
        """Initialize the bus arrival coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Bus arrivals",
            config_entry=config_entry,
            update_interval=timedelta(seconds=scan_interval),
            always_update=True,
        )
        self._sg_bus_arrivals = sg_bus_arrivals
        self._all_bus_services = {}

        async def _get_all_bus_services():
            self._all_bus_services = await self._sg_bus_arrivals.get_all_bus_services()

        # this is a slow api call so we are initializing it on start up
        self._task: Task = hass.async_create_task(
            _get_all_bus_services(), "get all bus services"
        )

    async def get_bus_services(self, bus_stop_code: str) -> set[str]:
        """Fetch all bus services for the specified bus stop."""
        await self._task
        return self._all_bus_services[bus_stop_code]

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        bus_stop_codes: set[str] = set()
        for subentry in self.config_entry.subentries.values():
            if subentry.subentry_type == SUBENTRY_TYPE_BUS_SERVICE:
                bus_stop_codes.add(subentry.data[SUBENTRY_CONF_BUS_STOP_CODE])

        all_bus_arrivals: dict[str, dict[str, BusArrival]] = collections.defaultdict(
            dict
        )
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with timeout(10):
                responses = await asyncio.gather(
                    *[
                        self._sg_bus_arrivals.get_bus_arrivals(bus_stop_code)
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
        except ApiAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except ApiGeneralError as err:
            raise UpdateFailed from err
