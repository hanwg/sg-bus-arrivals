"""Platform for sensor integration."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.components.sensor.const import SensorStateClass, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SgBusArrivalsConfigEntry
from .const import (
    RUNTIME_DATA_COORDINATOR,
    SUBENTRY_BUS_STOP_CODE,
    SUBENTRY_LABEL,
    SUBENTRY_SERVICE_NO,
)
from .coordinator import BusArrivalUpdateCoordinator
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
            coordinator,
            subentry.data[SUBENTRY_LABEL],
            subentry.data[SUBENTRY_BUS_STOP_CODE],
            subentry.data[SUBENTRY_SERVICE_NO],
        )
        async_add_entities([sensor], config_subentry_id=subentry.subentry_id)


# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


class BusArrivalSensor(CoordinatorEntity[BusArrivalUpdateCoordinator], SensorEntity):
    """Sensor tracking the number of minutes till bus arrival."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BusArrivalUpdateCoordinator,
        label: str,
        bus_stop_code: str,
        service_no: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._label = label
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_unique_id = f"{bus_stop_code}_{service_no}"
        self._attr_name = label
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_native_value = None
        self.entity_id = f"sensor.sgbusarrivals_{self._attr_unique_id}"
        self.icon = "mdi:bus-clock"
        self._bus_arrival = BusArrival(
            bus_stop_code=bus_stop_code,
            service_no=service_no,
            next_bus_minutes=coordinator.data[bus_stop_code][
                service_no
            ].next_bus_minutes,
            next_bus_minutes_2=coordinator.data[bus_stop_code][
                service_no
            ].next_bus_minutes_2,
            next_bus_minutes_3=coordinator.data[bus_stop_code][
                service_no
            ].next_bus_minutes_3,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        bus_arrival: BusArrival = self.coordinator.data[
            self._bus_arrival.bus_stop_code
        ][self._bus_arrival.service_no]
        self._bus_arrival = bus_arrival

        _LOGGER.debug(
            "Update sensor, bus_stop_code: %s, service_no: %s, data: %s",
            self._bus_arrival.bus_stop_code,
            self._bus_arrival.service_no,
            f"{self._bus_arrival.next_bus_minutes}/{self._bus_arrival.next_bus_minutes_2}/{self._bus_arrival.next_bus_minutes_3}",
        )
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        """Return the state of the entity."""
        return self._bus_arrival.next_bus_minutes

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        attrs = {}
        attrs["second_arrival_minutes"] = self._bus_arrival.next_bus_minutes_2
        attrs["third_arrival_minutes"] = self._bus_arrival.next_bus_minutes_3
        return attrs
