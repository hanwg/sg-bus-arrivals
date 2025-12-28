"""Options flow for the SG Bus Arrivals integration. Handle adding of new bus stop code."""

import logging
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigSubentry,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import SgBusArrivals
from .const import (
    SUBENTRY_CONF_BUS_STOP_CODE,
    SUBENTRY_CONF_DESCRIPTION,
    SUBENTRY_CONF_ROAD_NAME,
    SUBENTRY_CONF_SERVICE_NO,
    SUBENTRY_TYPE_BUS_SERVICE,
    SUBENTRY_TYPE_TRAIN_SERVICE_ALERTS,
)
from .coordinator import (
    BusArrivalsUpdateCoordinator,
    SgBusArrivalsConfigEntry,
    SgBusArrivalsData,
)
from .models import BusStop

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA: vol.Schema = vol.Schema(
    {vol.Required(SUBENTRY_CONF_BUS_STOP_CODE): str}
)


class TrainServiceAlertsSubEntryFlowHandler(ConfigSubentryFlow):
    """Handles subentry flow for creating train service alerts."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Create subentry."""
        config_entry: SgBusArrivalsConfigEntry = self._get_entry()
        for existing_subentry in config_entry.subentries.values():
            if existing_subentry.subentry_type == SUBENTRY_TYPE_TRAIN_SERVICE_ALERTS:
                return self.async_abort(reason="already_configured")

        return self.async_create_entry(
            title="Train Service Alerts",
            data={},
            unique_id=SUBENTRY_TYPE_TRAIN_SERVICE_ALERTS,
        )


class BusServiceSubEntryFlowHandler(ConfigSubentryFlow):
    """Handles subentry flow for creating new bus stops."""

    bus_stop_code: str
    road_name: str
    description: str
    new: bool = True

    async def _validate_bus_stop(
        self,
        data: str,
        errors: dict[str, str],
    ) -> BusStop | None:
        """Validate the user input allows us to connect.

        Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
        """
        config_entry: SgBusArrivalsConfigEntry = self._get_entry()
        sg_bus_arrivals_data: SgBusArrivalsData = config_entry.runtime_data
        sg_bus_arrivals: SgBusArrivals = sg_bus_arrivals_data.api
        bus_stop: BusStop | None = await sg_bus_arrivals.get_bus_stop(data)

        if bus_stop is None:
            errors["base"] = "invalid_bus_stop_code"

        return bus_stop

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Prompt user for bus stop code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            bus_stop: BusStop | None = await self._validate_bus_stop(
                user_input[SUBENTRY_CONF_BUS_STOP_CODE], errors
            )
            _LOGGER.debug("validate_bus_stop, bus_stop: %s", bus_stop)

            if not errors:
                assert bus_stop is not None
                self.bus_stop_code = bus_stop.bus_stop_code
                self.road_name = bus_stop.road_name
                self.description = bus_stop.description
                return await self.async_step_service_no(user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_service_no(
        self, user_input: dict[str, Any]
    ) -> SubentryFlowResult:
        """Prompt user for bus service number."""
        errors: dict[str, str] = {}

        config_entry: SgBusArrivalsConfigEntry = self._get_entry()
        sg_bus_arrivals_data: SgBusArrivalsData = config_entry.runtime_data
        coordinator: BusArrivalsUpdateCoordinator = (
            sg_bus_arrivals_data.bus_arrivals_coordinator
        )

        existing_service_nos: list[str] = [
            existing_subentry.data[SUBENTRY_CONF_SERVICE_NO]
            for existing_subentry in config_entry.subentries.values()
            if existing_subentry.subentry_type == SUBENTRY_TYPE_BUS_SERVICE
            and existing_subentry.data[SUBENTRY_CONF_BUS_STOP_CODE]
            == self.bus_stop_code
        ]

        bus_services = [
            service_no
            for service_no in await coordinator.get_bus_services(self.bus_stop_code)
            if service_no not in existing_service_nos
        ]

        if len(bus_services) < 1:
            return self.async_abort(reason="already_configured")

        if SUBENTRY_CONF_SERVICE_NO in user_input:
            for service_no in user_input[SUBENTRY_CONF_SERVICE_NO]:
                self.hass.config_entries.async_add_subentry(
                    config_entry,
                    ConfigSubentry(
                        data=MappingProxyType(
                            {
                                SUBENTRY_CONF_SERVICE_NO: service_no,
                                SUBENTRY_CONF_BUS_STOP_CODE: self.bus_stop_code,
                                SUBENTRY_CONF_DESCRIPTION: self.description,
                            }
                        ),
                        subentry_type=SUBENTRY_TYPE_BUS_SERVICE,
                        title=f"{service_no} @{self.description}",
                        unique_id=f"{self.bus_stop_code}_{service_no}",
                    ),
                )

            return self.async_abort(
                reason="subentries_created",
                description_placeholders={
                    "service_nos": ", ".join(user_input[SUBENTRY_CONF_SERVICE_NO]),
                },
            )

        if not self.new:
            errors["base"] = "no_service_no_selected"
        self.new = False
        return self.async_show_form(
            step_id="service_no",
            data_schema=vol.Schema(
                {
                    vol.Optional(SUBENTRY_CONF_SERVICE_NO): SelectSelector(
                        SelectSelectorConfig(
                            options=bus_services,
                            mode=SelectSelectorMode.LIST,
                            multiple=True,
                            sort=True,
                        )
                    )
                }
            ),
            description_placeholders={
                SUBENTRY_CONF_ROAD_NAME: self.road_name,
                SUBENTRY_CONF_DESCRIPTION: self.description,
            },
            errors=errors,
        )
