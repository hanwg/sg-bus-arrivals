"""Platform for sensor integration."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.components.sensor.const import SensorStateClass, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SgBusArrivalsConfigEntry
from .const import (
    RUNTIME_DATA_COORDINATOR,
    SUBENTRY_BUS_STOP_CODE,
    SUBENTRY_LABEL,
    SUBENTRY_SERVICE_NO,
)
from .coordinator import BusArrivalUpdateCoordinator
from .entity import BusArrivalEntity
from .model.bus_arrival import BusArrival

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SgBusArrivalsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""

    # retrieve our api instance
    coordinator: BusArrivalUpdateCoordinator = config_entry.runtime_data[
        RUNTIME_DATA_COORDINATOR
    ]

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    for subentry in config_entry.subentries.values():
        sensor: BusArrivalSensor = BusArrivalSensor(
            config_entry,
            subentry.data[SUBENTRY_LABEL],
            subentry.data[SUBENTRY_BUS_STOP_CODE],
            subentry.data[SUBENTRY_SERVICE_NO],
        )
        async_add_entities([sensor], config_subentry_id=subentry.subentry_id)


# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


class BusArrivalSensor(BusArrivalEntity, SensorEntity):
    """Sensor tracking the number of minutes till bus arrival."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: SgBusArrivalsConfigEntry,
        label: str,
        bus_stop_code: str,
        service_no: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(config_entry)

        self.entity_id = f"sensor.sgbusarrivals_{self._attr_unique_id}"
        self.icon = "mdi:bus-clock"

        self._label = label
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_unique_id = f"{bus_stop_code}_{service_no}"
        self._attr_name = label
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_native_value = None
        self._bus_stop_code = bus_stop_code
        self._service_no = service_no

    def _get_data(self, bus_stop_code: str, service_no: str) -> BusArrival:
        if service_no in self.coordinator.data[bus_stop_code]:
            return self.coordinator.data[bus_stop_code][service_no]

        return BusArrival(
            bus_stop_code=bus_stop_code,
            service_no=service_no,
            next_bus_minutes=None,
            next_bus_minutes_2=None,
            next_bus_minutes_3=None,
        )

    @property
    def native_value(self) -> int:
        """Return the state of the entity."""
        bus_arrival: BusArrival = self._get_data(
            self._bus_stop_code, self._service_no
        )
        _LOGGER.debug(
            "Update sensor, bus_stop_code: %s, service_no: %s, arrivals: %s",
            self._bus_stop_code,
            self._service_no,
            f"{bus_arrival.next_bus_minutes}/{bus_arrival.next_bus_minutes_2}/{bus_arrival.next_bus_minutes_3}",
        )
        return bus_arrival.next_bus_minutes
