"""Tests for sensor."""

from unittest.mock import MagicMock

from custom_components.sg_bus_arrivals.models import BusArrival
from custom_components.sg_bus_arrivals.sensor import BusArrivalSensor


async def test_get_data_not_found() -> None:
    """Test the get_data method."""
    bus_stop_code: str = "mock_bus_stop_code"
    service_no: str = "mock_service_no"
    bus_arrivals: dict[str, BusArrival] = {bus_stop_code: {}}

    entity = BusArrivalSensor(MagicMock(), MagicMock(), MagicMock(), bus_stop_code, "mock description", service_no)

    result: BusArrival = entity._get_data(bus_arrivals, service_no)  # noqa: SLF001

    assert result.next_bus == []
