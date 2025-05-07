"""Options flow for the SG Bus Arrivals integration. Handle adding of new bus stop code."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigSubentryFlow,
    SubentryFlowResult,
)

from .const import SUBENTRY_BUS_STOP_CODE, SUBENTRY_SERVICE_NO
from .model.bus_stop import BusStop
from .sg_bus_arrivals_service import SgBusArrivalsService

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(SUBENTRY_BUS_STOP_CODE): str, vol.Required(SUBENTRY_SERVICE_NO): str}
)


async def validate_bus_stop(
    config_entry: ConfigEntry,
    data: str,
    errors: dict[str, str],
) -> BusStop:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    service: SgBusArrivalsService = config_entry.runtime_data
    bus_stop: BusStop = await service.get_bus_stop(data)

    if bus_stop is None:
        errors["base"] = "invalid_bus_stop_code"

    return bus_stop


class BusServiceSubEntryFlowHandler(ConfigSubentryFlow):
    """Handles options flow for creating new bus stops."""

    @property
    def config_entry(self):
        """Return the config entry."""
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle adding of new bus stop code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            config_entry = self._get_entry()
            for existing_subentry in config_entry.subentries.values():
                if (
                    existing_subentry.unique_id
                    == f"{user_input[SUBENTRY_BUS_STOP_CODE]}_{user_input[SUBENTRY_SERVICE_NO]}"
                ):
                    return self.async_abort(reason="already_configured")

            bus_stop: BusStop = await validate_bus_stop(
                config_entry, user_input[SUBENTRY_BUS_STOP_CODE], errors
            )

            if not errors:
                return self.async_create_entry(
                    title=bus_stop.description,
                    data=user_input,
                    unique_id=f"{user_input[SUBENTRY_BUS_STOP_CODE]}_{user_input[SUBENTRY_SERVICE_NO]}",
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
