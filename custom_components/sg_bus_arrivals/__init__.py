"""The SG Bus Arrivals integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant

from .api import SgBusArrivalsService
from .coordinator import BusArrivalUpdateCoordinator, SgBusArrivalsConfigEntry

_PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, entry: SgBusArrivalsConfigEntry
) -> bool:
    """Set up SG Bus Arrivals from a config entry."""

    # create instance of our api
    service: SgBusArrivalsService = SgBusArrivalsService(entry.data[CONF_API_KEY])
    coordinator: BusArrivalUpdateCoordinator = BusArrivalUpdateCoordinator(
        hass, entry, service, entry.data[CONF_SCAN_INTERVAL]
    )

    await service.authenticate()

    # store reference to our api so that sensor entites can use it
    entry.runtime_data = coordinator

    # Registers update listener to update config entry when options are updated.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # pass config to sensor.py to create sensor entites
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: SgBusArrivalsConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
