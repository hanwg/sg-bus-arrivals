"""Bus Arrival entity."""

from collections.abc import Mapping
from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import (
    BusArrivalUpdateCoordinator,
    TrainServiceAlertsUpdateCoordinator,
)
from .models import BusArrival


class TrainServiceAlertEntity(CoordinatorEntity[TrainServiceAlertsUpdateCoordinator]):
    """Train service alert entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TrainServiceAlertsUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)


class BusArrivalEntity(CoordinatorEntity[BusArrivalUpdateCoordinator]):
    """Bus arrival entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BusArrivalUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the extra state attributes."""

        bus_arrival: BusArrival = self._get_data(self._bus_stop_code, self._service_no)

        attrs: Mapping[str, Any] = {}
        attrs["bus_stop_code"] = bus_arrival.bus_stop_code
        attrs["service_no"] = bus_arrival.service_no
        return attrs
