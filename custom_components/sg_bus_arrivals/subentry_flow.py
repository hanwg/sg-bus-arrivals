"""Options flow for the SG Bus Arrivals integration. Handle adding of new bus stop code."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigSubentryFlow, SubentryFlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import SgBusArrivalsService
from .const import (
    SUBENTRY_BUS_STOP_CODE,
    SUBENTRY_DESCRIPTION,
    SUBENTRY_ROAD_NAME,
    SUBENTRY_SERVICE_NO,
)
from .coordinator import BusArrivalUpdateCoordinator, SgBusArrivalsConfigEntry
from .models import BusStop

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA: vol.Schema = vol.Schema(
    {vol.Required(SUBENTRY_BUS_STOP_CODE): str}
)


class BusServiceSubEntryFlowHandler(ConfigSubentryFlow):
    """Handles options flow for creating new bus stops."""

    bus_stop_code: str
    road_name: str
    description: str

    def _get_service(self) -> SgBusArrivalsService:
        config_entry: SgBusArrivalsConfigEntry = self._get_entry()
        coordinator: BusArrivalUpdateCoordinator = config_entry.runtime_data
        return coordinator.get_service()

    async def _validate_bus_stop(
        self,
        data: str,
        errors: dict[str, str],
    ) -> BusStop:
        """Validate the user input allows us to connect.

        Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
        """
        service: SgBusArrivalsService = self._get_service()
        bus_stop: BusStop = await service.get_bus_stop(data)

        if bus_stop is None:
            errors["base"] = "invalid_bus_stop_code"

        return bus_stop

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Prompt user for bus stop code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            bus_stop: BusStop = await self._validate_bus_stop(
                user_input[SUBENTRY_BUS_STOP_CODE], errors
            )
            _LOGGER.debug("validate_bus_stop, bus_stop: %s", bus_stop)

            if not errors:
                self.bus_stop_code = bus_stop.bus_stop_code
                self.road_name = bus_stop.road_name
                self.description = bus_stop.description
                return await self.async_step_service_no(user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_service_no(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Prompt user for bus service number."""
        errors: dict[str, str] = {}
        config_entry: SgBusArrivalsConfigEntry = self._get_entry()
        if SUBENTRY_SERVICE_NO in user_input:
            for existing_subentry in config_entry.subentries.values():
                if (
                    existing_subentry.unique_id
                    == f"{self.bus_stop_code}_{user_input[SUBENTRY_SERVICE_NO]}"
                ):
                    return self.async_abort(reason="already_configured")

            user_input[SUBENTRY_BUS_STOP_CODE] = self.bus_stop_code
            user_input[SUBENTRY_DESCRIPTION] = self.description
            return self.async_create_entry(
                title=f"{user_input[SUBENTRY_SERVICE_NO]} @{self.description}",
                data=user_input,
                unique_id=f"{self.bus_stop_code}_{user_input[SUBENTRY_SERVICE_NO]}",
            )

        coordinator: BusArrivalUpdateCoordinator = config_entry.runtime_data
        bus_services: list[str] = await coordinator.get_bus_services(self.bus_stop_code)

        return self.async_show_form(
            step_id="service_no",
            data_schema=vol.Schema(
                {
                    vol.Required(SUBENTRY_SERVICE_NO): SelectSelector(
                        SelectSelectorConfig(
                            options=sorted(bus_services),
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            description_placeholders={
                SUBENTRY_ROAD_NAME: self.road_name,
                SUBENTRY_DESCRIPTION: self.description,
            },
            errors=errors,
        )
