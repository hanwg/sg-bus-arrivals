"""Config flow for the SG Bus Arrivals integration. Configures the Account Key for the API."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, callback

from .bus_service_subentry_flow import BusServiceSubEntryFlowHandler
from .const import DOMAIN
from .sg_bus_arrivals_service import SgBusArrivalsService

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_API_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


async def validate_api(
    hass: HomeAssistant, data: dict[str, Any], errors: dict[str, str]
) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    service = SgBusArrivalsService(data[CONF_API_KEY])

    if not await service.authenticate():
        errors["base"] = "invalid_auth"

    return errors


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SG Bus Arrivals."""

    VERSION = 1

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {"bus_service": BusServiceSubEntryFlowHandler}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        if user_input is not None:
            await validate_api(self.hass, user_input, errors)
            if not errors:
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data_updates=user_input
                    )

                return self.async_create_entry(
                    title="LTA DataMall API", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_API_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Re-authenticate API."""

        errors: dict[str, str] = {}
        if user_input is not None:
            self._abort_if_unique_id_mismatch()

            await validate_api(self.hass, user_input, errors)

            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(), data_updates=user_input
                )

        return self.async_show_form(
            step_id="reconfigure", data_schema=STEP_USER_DATA_API_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""

        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=STEP_USER_DATA_API_SCHEMA,
            )
        return await self.async_step_user()
