"""The SG Bus Arrivals integration."""

from __future__ import annotations

from aiohttp import ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApiAuthenticationError, SgBusArrivalsService
from .const import DOMAIN, SERVICE_REFRESH_BUS_ARRIVALS
from .coordinator import BusArrivalUpdateCoordinator, SgBusArrivalsConfigEntry

_PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, entry: SgBusArrivalsConfigEntry
) -> bool:
    """Set up SG Bus Arrivals from a config entry."""

    # create instance of our api
    session: ClientSession = async_get_clientsession(hass)
    service: SgBusArrivalsService = SgBusArrivalsService(
        session, entry.data[CONF_API_KEY]
    )
    coordinator: BusArrivalUpdateCoordinator = BusArrivalUpdateCoordinator(
        hass, entry, service, entry.data[CONF_SCAN_INTERVAL]
    )

    try:
        await service.authenticate()
    except ApiAuthenticationError as e:
        raise ConfigEntryAuthFailed from e

    # store reference to our api so that sensor entites can use it
    entry.runtime_data = service

    # Registers update listener to update config entry when options are updated.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def refresh_bus_arrivals(call) -> None:
        """Service call to refresh the bus arrivals."""
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH_BUS_ARRIVALS, refresh_bus_arrivals
    )

    # pass config to sensor.py to create sensor entites
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: SgBusArrivalsConfigEntry
) -> bool:
    """Unload services and config entry."""

    isUnloaded: bool = await hass.config_entries.async_unload_platforms(
        entry, _PLATFORMS
    )

    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_BUS_ARRIVALS)

    return isUnloaded
