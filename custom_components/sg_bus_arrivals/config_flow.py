"""Config flow for the SG Bus Arrivals integration. Configures the Account Key for the API."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from aiohttp import ClientSession
import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
)
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ApiAuthenticationError, ApiGeneralError, SgBusArrivals
from .const import (
    DOMAIN,
    MIN_SCAN_INTERVAL_SECONDS,
    SUBENTRY_TYPE_BUS_SERVICE,
    SUBENTRY_TYPE_TRAIN_SERVICE_ALERTS,
)
from .coordinator import SgBusArrivalsData
from .subentry_flow import (
    BusServiceSubEntryFlowHandler,
    TrainServiceAlertsSubEntryFlowHandler,
)

_LOGGER = logging.getLogger(__name__)


def get_data_schema(
    api_key: str | None = None, scan_interval: int = MIN_SCAN_INTERVAL_SECONDS
) -> vol.Schema:
    """Return the schema for the config flow."""
    return vol.Schema(
        {
            vol.Required(CONF_API_KEY, default=api_key): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
            vol.Required(CONF_SCAN_INTERVAL, default=scan_interval): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_SECONDS)
            ),
        }
    )


class SgBusArrivalsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SG Bus Arrivals."""

    VERSION = 1

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {
            SUBENTRY_TYPE_BUS_SERVICE: BusServiceSubEntryFlowHandler,
            SUBENTRY_TYPE_TRAIN_SERVICE_ALERTS: TrainServiceAlertsSubEntryFlowHandler,
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        if user_input is not None:
            await self.validate_api(user_input, errors)
            if not errors:
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data_updates=user_input
                    )

                return self.async_create_entry(
                    title="LTA DataMall API", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=get_data_schema(), errors=errors
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Re-authenticate API."""

        errors: dict[str, str] = {}
        if user_input is not None:
            self._abort_if_unique_id_mismatch()

            await self.validate_api(user_input, errors)

            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(), data_updates=user_input
                )

        api_key: str = self._get_reconfigure_entry().data[CONF_API_KEY]
        scan_interval: str = self._get_reconfigure_entry().data[CONF_SCAN_INTERVAL]
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_data_schema(api_key, scan_interval),
            errors=errors,
        )

    async def validate_api(self, data: dict[str, Any], errors: dict[str, str]) -> None:
        """Validate the user input allows us to connect to the API."""

        sg_bus_arrivals: SgBusArrivals = None
        config_entries: list[ConfigEntry[SgBusArrivalsData]] = self._async_current_entries()
        if config_entries:
            sg_bus_arrivals_data: SgBusArrivalsData = config_entries[0].runtime_data
            sg_bus_arrivals = sg_bus_arrivals_data.api
        else:
            session: ClientSession = async_get_clientsession(self.hass)
            sg_bus_arrivals = SgBusArrivals(session, data[CONF_API_KEY])

        try:
            await sg_bus_arrivals.authenticate()
        except ApiAuthenticationError:
            errors["base"] = "invalid_auth"
        except ApiGeneralError:
            errors["base"] = "cannot_connect"

        return errors

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
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_API_KEY): TextSelector(
                            TextSelectorConfig(
                                type=TextSelectorType.PASSWORD,
                                autocomplete="current-password",
                            )
                        )
                    }
                ),
            )
        return await self.async_step_user()
