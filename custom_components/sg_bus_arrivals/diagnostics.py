"""Diagnostics support for SG Bus Arrivals."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .const import (
    SUBENTRY_CONF_BUS_STOP_CODE,
    SUBENTRY_CONF_SERVICE_NO,
    SUBENTRY_TYPE_TRAIN_SERVICE_ALERTS,
)
from .coordinator import SgBusArrivalsConfigEntry

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: SgBusArrivalsConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    diagnostics: dict[str, Any] = {
        "config_entry_data": async_redact_data(dict(config_entry.data), TO_REDACT),
        "bus_services": []
    }

    # collect subentry info
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_TRAIN_SERVICE_ALERTS:
            diagnostics["train_service_alerts"] = "True"
        else:
            diagnostics["bus_services"].append({
                SUBENTRY_CONF_BUS_STOP_CODE: subentry.data[SUBENTRY_CONF_BUS_STOP_CODE],
                SUBENTRY_CONF_SERVICE_NO: subentry.data[SUBENTRY_CONF_SERVICE_NO]
            })

    return diagnostics
