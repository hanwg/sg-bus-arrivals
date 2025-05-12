"""Platform for sensor integration."""

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.components.sensor.const import SensorStateClass, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SgBusArrivalsConfigEntry
from .const import SUBENTRY_BUS_STOP_CODE, SUBENTRY_LABEL, SUBENTRY_SERVICE_NO
from .coordinator import BusArrivalUpdateCoordinator
from .entity import BusArrivalEntity
from .models import BusArrival

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SgBusArrivalsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""

    # retrieve our api instance
    coordinator: BusArrivalUpdateCoordinator = config_entry.runtime_data

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    for subentry in config_entry.subentries.values():
        sensors: list[BusArrivalSensor] = [
            BusArrivalSensor(
                config_entry,
                sensor_description,
                subentry.data[SUBENTRY_BUS_STOP_CODE],
                subentry.data[SUBENTRY_LABEL],
                subentry.data[SUBENTRY_SERVICE_NO],
            )
            for sensor_description in SENSOR_DESCRIPTIONS
        ]

        async_add_entities(
            sensors, update_before_add=True, config_subentry_id=subentry.subentry_id
        )


# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SgBusArrivalsSensorDescription(SensorEntityDescription):
    """Describes the bus arrival sensor entity."""

    icon: str
    value_fn: Callable[[BusArrival], int | None]


SENSOR_DESCRIPTIONS: tuple[SgBusArrivalsSensorDescription] = (
    SgBusArrivalsSensorDescription(
        key="1st_arrival",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:numeric-1-circle",
        value_fn=lambda bus_arrival: bus_arrival.next_bus_minutes,
        translation_key="1st_arrival"
    ),
    SgBusArrivalsSensorDescription(
        key="2nd_arrival",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:numeric-2-circle",
        value_fn=lambda bus_arrival: bus_arrival.next_bus_minutes_2,
        translation_key="2nd_arrival"
    ),
    SgBusArrivalsSensorDescription(
        key="3rd_arrival",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:numeric-3-circle",
        value_fn=lambda bus_arrival: bus_arrival.next_bus_minutes_3,
        translation_key="3rd_arrival"
    ),
)


class BusArrivalSensor(BusArrivalEntity, SensorEntity):
    """Sensor tracking the number of minutes till bus arrival."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: SgBusArrivalsConfigEntry,
        entity_description: SgBusArrivalsSensorDescription,
        bus_stop_code: str,
        description: str,
        service_no: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(config_entry)
        self.entity_description = entity_description

        self.translation_placeholders = {
            "bus_stop_code": bus_stop_code,
            "service_no": service_no,
            "description": description
        }

        self._attr_unique_id = f"{bus_stop_code}_{service_no}_{entity_description.key}"
        self.entity_id = f"sensor.sgbusarrivals_{self._attr_unique_id}"
        self.icon = entity_description.icon
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
        bus_arrival: BusArrival = self._get_data(self._bus_stop_code, self._service_no)
        _LOGGER.debug(
            "Update sensor, bus_stop_code: %s, service_no: %s, arrivals: %s",
            self._bus_stop_code,
            self._service_no,
            f"{bus_arrival.next_bus_minutes}/{bus_arrival.next_bus_minutes_2}/{bus_arrival.next_bus_minutes_3}",
        )
        return self.entity_description.value_fn(bus_arrival)
