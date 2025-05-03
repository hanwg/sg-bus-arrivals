"""Options flow for the SG Bus Arrivals integration. Handle adding of new bus stop code."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .model.bus_stop import BusStop
from .sg_bus_arrivals_service import SgBusArrivalsService

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required("bus_stop_code"): str})


async def validate_bus_stop(
    config_entry: config_entries.ConfigEntry,
    data: str,
    errors: dict[str, str],
) -> BusStop:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    service: SgBusArrivalsService = config_entry.runtime_data
    bus_stop: BusStop = await service.get_bus_stop(data)

    x = await service.get_bus_services(bus_stop.bus_stop_code)
    if bus_stop is None:
        errors["base"] = "invalid_bus_stop_code"

    return bus_stop


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for creating new bus stops."""

    @property
    def config_entry(self):
        """Return the config entry."""
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding of new bus stop code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            bus_stop: BusStop = await validate_bus_stop(
                self.config_entry, user_input["bus_stop_code"], errors
            )

            if not errors:
                return self.async_create_entry(
                    title=bus_stop.description, data=user_input
                )

        return self.async_show_form(
            step_id="init", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
