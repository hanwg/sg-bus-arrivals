"""Diagnostics support for SG Bus Arrivals."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .coordinator import SgBusArrivalsConfigEntry

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: SgBusArrivalsConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    return {
        "config_entry_data": async_redact_data(dict(config_entry.data), TO_REDACT)
    }
