"""Tests for the config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.sg_bus_arrivals.const import DOMAIN, SUBENTRY_TYPE
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant


@patch(
    "custom_components.sg_bus_arrivals.sg_bus_arrivals_service.SgBusArrivalsService.authenticate",
    new_callable=AsyncMock,
)
@patch(
    "custom_components.sg_bus_arrivals.sg_bus_arrivals_service.SgBusArrivalsService.get_bus_stop",
    new_callable=AsyncMock,
)
async def test_async_step_init_fail(
    mock_get_bus_stop: MagicMock, mock_authenticate: MagicMock, hass: HomeAssistant
) -> None:
    """Test user flow - invalid bus stop code."""

    mock_authenticate.return_value = True

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test_api",
        data={CONF_API_KEY: "dummy account key"},
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_authenticate.called

    mock_get_bus_stop.return_value = None

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, SUBENTRY_TYPE),
        context={"source": SOURCE_USER},
        data={"bus_stop_code": "invalid bus stop code"},
    )

    assert mock_get_bus_stop.called
    assert result["errors"] == {"base": "invalid_bus_stop_code"}
