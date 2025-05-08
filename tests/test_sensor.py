"""Tests for sensor."""

from unittest.mock import MagicMock, patch

from custom_components.sg_bus_arrivals.model.bus_arrival import BusArrival
from custom_components.sg_bus_arrivals.sensor import BusArrivalSensor


@patch("custom_components.sg_bus_arrivals.sensor.BusArrivalSensor.async_write_ha_state")
async def test_handle_coordinator_update(mock: MagicMock) -> None:
    """Test the handle_coordinator_update."""
    mock_coordinator = MagicMock()

    bus_stop_code: str = "mock_bus_stop_code"
    service_no: str = "mock_service_no"
    mock_coordinator.data = {
        bus_stop_code: {
            service_no: BusArrival(bus_stop_code, service_no, 123, 456, 789)
        }
    }

    entity = BusArrivalSensor(mock_coordinator, "mock label", bus_stop_code, service_no)

    # Call the handle_coordinator_update method
    entity._handle_coordinator_update()  # noqa: SLF001

    assert mock.called
    assert entity._bus_arrival.next_bus_minutes == 123  # noqa: SLF001
    assert entity._bus_arrival.next_bus_minutes_2 == 456  # noqa: SLF001
    assert entity._bus_arrival.next_bus_minutes_3 == 789  # noqa: SLF001


async def test_get_data_not_found() -> None:
    """Test the get_data method."""
    bus_stop_code: str = "mock_bus_stop_code"
    service_no: str = "mock_service_no"
    bus_arrivals: dict[str, BusArrival] = {bus_stop_code: {}}

    entity = BusArrivalSensor(MagicMock(), "mock label", bus_stop_code, service_no)

    result = entity._get_data(bus_arrivals, service_no)  # noqa: SLF001

    assert result.next_bus_minutes is None
    assert result.next_bus_minutes_2 is None
    assert result.next_bus_minutes_3 is None
