"""Tests for the config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.sg_bus_arrivals.const import DOMAIN, MIN_SCAN_INTERVAL_SECONDS

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed


@patch(
    "custom_components.sg_bus_arrivals.api.SgBusArrivalsService.authenticate",
    new_callable=AsyncMock,
)
async def test_user_flow_fail_authenticate(
    mock: MagicMock, hass: HomeAssistant
) -> None:
    """Test user flow - authentication failed."""

    mock.side_effect = ConfigEntryAuthFailed()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_API_KEY: "invalid_key",
            CONF_SCAN_INTERVAL: MIN_SCAN_INTERVAL_SECONDS,
        },
    )

    assert mock.called
    assert result["errors"] == {"base": "invalid_auth"}
