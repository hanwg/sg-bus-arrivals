"""Tests for the config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.sg_bus_arrivals.const import DOMAIN

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed


@patch(
    "custom_components.sg_bus_arrivals.sg_bus_arrivals_service.SgBusArrivalsService.authenticate",
    new_callable=AsyncMock,
)
async def test_user_flow_fail(mock: MagicMock, hass: HomeAssistant) -> None:
    """Test user flow - authentication failed."""

    mock.side_effect = ConfigEntryAuthFailed()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"api_key": "invalid_key"}
    )

    assert mock.called
    assert result["errors"] == {"base": "invalid_auth"}
