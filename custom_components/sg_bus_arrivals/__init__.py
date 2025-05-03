"""The SG Bus Arrivals integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from . import sg_bus_arrivals_service

_PLATFORMS: list[Platform] = [Platform.SENSOR]

type SgBusArrivalsConfigEntry = ConfigEntry[
    sg_bus_arrivals_service.SgBusArrivalsService
]


async def async_setup_entry(
    hass: HomeAssistant, entry: SgBusArrivalsConfigEntry
) -> bool:
    """Set up SG Bus Arrivals from a config entry."""

    # create instance of our api
    service = sg_bus_arrivals_service.SgBusArrivalsService(
        hass, entry.data[CONF_API_KEY]
    )

    result = await service.authenticate()
    if not result:
        raise ConfigEntryAuthFailed

    # store reference to our api so that sensor entites can use it
    entry.runtime_data = service

    # pass config to sensor.py to create sensor entites
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SgBusArrivalsConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
