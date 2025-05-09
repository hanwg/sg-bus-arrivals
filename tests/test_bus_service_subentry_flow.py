"""Tests for the config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.sg_bus_arrivals.const import (
    DOMAIN,
    MIN_SCAN_INTERVAL_SECONDS,
    SUBENTRY_BUS_STOP_CODE,
    SUBENTRY_LABEL,
    SUBENTRY_SERVICE_NO,
    SUBENTRY_TYPE,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from config.custom_components.sg_bus_arrivals.model.bus_arrival import BusArrival
from config.custom_components.sg_bus_arrivals.model.bus_stop import BusStop
from homeassistant.config_entries import SOURCE_USER, ConfigSubentryData
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant


@patch(
    "custom_components.sg_bus_arrivals.sg_bus_arrivals_service.SgBusArrivalsService.authenticate",
    new_callable=AsyncMock,
)
@patch(
    "custom_components.sg_bus_arrivals.sg_bus_arrivals_service.SgBusArrivalsService.get_bus_stop",
    new_callable=AsyncMock,
)
async def test_async_step_init(
    mock_get_bus_stop: MagicMock, mock_authenticate: MagicMock, hass: HomeAssistant
) -> None:
    """Test user flow - invalid bus stop code."""

    mock_authenticate.return_value = True

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test_api",
        data={CONF_API_KEY: "dummy account key", CONF_SCAN_INTERVAL: MIN_SCAN_INTERVAL_SECONDS},
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_authenticate.called

    mock_get_bus_stop.return_value = BusStop(
        "mock_bus_stop_code", "mock_road_name", "mock_description"
    )

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, SUBENTRY_TYPE),
        context={"source": SOURCE_USER},
        data={
            SUBENTRY_BUS_STOP_CODE: "mock_bus_stop_code",
            SUBENTRY_LABEL: "mock_label",
            SUBENTRY_SERVICE_NO: "mock_service_no",
        },
    )
    await hass.async_block_till_done()

    assert mock_get_bus_stop.called
    assert result["result"]


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
        data={CONF_API_KEY: "dummy account key", CONF_SCAN_INTERVAL: MIN_SCAN_INTERVAL_SECONDS},
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_authenticate.called

    mock_get_bus_stop.return_value = None

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, SUBENTRY_TYPE),
        context={"source": SOURCE_USER},
        data={SUBENTRY_BUS_STOP_CODE: "invalid bus stop code"},
    )

    assert mock_get_bus_stop.called
    assert result["errors"] == {"base": "invalid_bus_stop_code"}


@patch(
    "custom_components.sg_bus_arrivals.sg_bus_arrivals_service.SgBusArrivalsService.authenticate",
    new_callable=AsyncMock,
)
@patch(
    "custom_components.sg_bus_arrivals.sg_bus_arrivals_service.SgBusArrivalsService.get_bus_arrivals",
    new_callable=AsyncMock,
)
async def test_async_step_init_duplicate(
    mock_get_bus_arrivals: MagicMock,
    mock_authenticate: MagicMock,
    hass: HomeAssistant,
) -> None:
    """Test user flow - invalid bus stop code."""

    mock_authenticate.return_value = True

    bus_stop_code: str = "123"
    service_no: str = "456"

    mock_get_bus_arrivals.return_value = [
        BusArrival(bus_stop_code, service_no, None, None, None)
    ]

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test_api",
        data={CONF_API_KEY: "mock account key", CONF_SCAN_INTERVAL: MIN_SCAN_INTERVAL_SECONDS},
        subentries_data=[
            ConfigSubentryData(
                data={
                    SUBENTRY_LABEL: "mock label",
                    SUBENTRY_BUS_STOP_CODE: bus_stop_code,
                    SUBENTRY_SERVICE_NO: service_no,
                },
                subentry_id="mock subentry id",
                subentry_type=SUBENTRY_TYPE,
                title="mock subentry",
                unique_id=f"{bus_stop_code}_{service_no}",
            )
        ],
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_authenticate.called

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, SUBENTRY_TYPE),
        context={"source": SOURCE_USER},
        data={SUBENTRY_BUS_STOP_CODE: bus_stop_code, SUBENTRY_SERVICE_NO: service_no},
    )

    assert mock_get_bus_arrivals.called
    assert result["reason"] == "already_configured"
