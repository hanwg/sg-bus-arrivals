"""Options flow for the SG Bus Arrivals integration. Handle adding of new bus stop code."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigSubentryFlow,
    SubentryFlowResult,
)

from .api import SgBusArrivalsService
from .const import SUBENTRY_BUS_STOP_CODE, SUBENTRY_LABEL, SUBENTRY_SERVICE_NO
from .coordinator import BusArrivalUpdateCoordinator, SgBusArrivalsConfigEntry
from .models import BusStop

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA: vol.Schema = vol.Schema(
    {
        vol.Required(SUBENTRY_LABEL): str,
        vol.Required(SUBENTRY_BUS_STOP_CODE): str,
        vol.Required(SUBENTRY_SERVICE_NO): str,
    }
)


async def validate_bus_stop(
    config_entry: ConfigEntry,
    data: str,
    errors: dict[str, str],
) -> BusStop:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    coordinator: BusArrivalUpdateCoordinator = config_entry.runtime_data
    service: SgBusArrivalsService = coordinator.get_service()
    bus_stop: BusStop = await service.get_bus_stop(data)

    if bus_stop is None:
        errors["base"] = "invalid_bus_stop_code"

    return bus_stop


class BusServiceSubEntryFlowHandler(ConfigSubentryFlow):
    """Handles options flow for creating new bus stops."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle adding of new bus stop code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            config_entry: SgBusArrivalsConfigEntry = self._get_entry()
            for existing_subentry in config_entry.subentries.values():
                if (
                    existing_subentry.unique_id
                    == f"{user_input[SUBENTRY_BUS_STOP_CODE]}_{user_input[SUBENTRY_SERVICE_NO]}"
                ):
                    return self.async_abort(reason="already_configured")

            bus_stop: BusStop = await validate_bus_stop(
                config_entry, user_input[SUBENTRY_BUS_STOP_CODE], errors
            )
            _LOGGER.debug("validate_bus_stop, bus_stop: %s", bus_stop)

            if not errors:
                return self.async_create_entry(
                    title=user_input[SUBENTRY_LABEL],
                    data=user_input,
                    unique_id=f"{user_input[SUBENTRY_BUS_STOP_CODE]}_{user_input[SUBENTRY_SERVICE_NO]}",
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
