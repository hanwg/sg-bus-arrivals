"""Bus Arrival entity."""

from collections.abc import Mapping
from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SgBusArrivalsConfigEntry
from .coordinator import BusArrivalUpdateCoordinator
from .models import BusArrival


class BusArrivalEntity(CoordinatorEntity[BusArrivalUpdateCoordinator]):
    """Entity."""

    _attr_has_entity_name = True

    def __init__(self, config_entry: SgBusArrivalsConfigEntry) -> None:
        """Initialize."""
        super().__init__(config_entry.runtime_data)
        self._entry = config_entry

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the extra state attributes."""

        bus_arrival: BusArrival = self._get_data(self._bus_stop_code, self._service_no)

        attrs: Mapping[str, Any] = {}
        attrs["bus_stop_code"] = bus_arrival.bus_stop_code
        attrs["service_no"] = bus_arrival.service_no
        return attrs
