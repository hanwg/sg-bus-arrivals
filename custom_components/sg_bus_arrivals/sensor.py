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
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SgBusArrivalsConfigEntry
from .const import DOMAIN, SUBENTRY_BUS_STOP_CODE, SUBENTRY_LABEL, SUBENTRY_SERVICE_NO
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
                subentry,
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

    cardinality: int
    icon: str
    value_fn: Callable[[int, BusArrival], int | None]


def _get_sensor_descriotions() -> list[SgBusArrivalsSensorDescription]:
    sensor_descriptions = []
    for i in range(1, 4):
        sensor_descriptions.append(
            SgBusArrivalsSensorDescription(
                cardinality=i,
                key=f"next_bus_{i}_estimated_arrival",
                native_unit_of_measurement=UnitOfTime.MINUTES,
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                icon="mdi:bus-clock",
                value_fn=lambda cardinality, bus_arrival: bus_arrival.next_bus[
                    cardinality - 1
                ].estimated_arrival_minutes,
                translation_key=f"next_bus_{i}_estimated_arrival",
            )
        )

        sensor_descriptions.append(
            SgBusArrivalsSensorDescription(
                cardinality=i,
                key=f"next_bus_{i}_bus_type",
                device_class=SensorDeviceClass.ENUM,
                value_fn=lambda cardinality, bus_arrival: bus_arrival.next_bus[
                    cardinality - 1
                ].bus_type,
                translation_key=f"next_bus_{i}_bus_type",
            )
        )

    return sensor_descriptions


SENSOR_DESCRIPTIONS: list[SgBusArrivalsSensorDescription] = _get_sensor_descriotions()


class BusArrivalSensor(BusArrivalEntity, SensorEntity):
    """Sensor tracking the number of minutes till bus arrival."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: SgBusArrivalsConfigEntry,
        subentry: ConfigSubentry,
        entity_description: SgBusArrivalsSensorDescription,
        bus_stop_code: str,
        description: str,
        service_no: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(config_entry)
        self.entity_description = entity_description

        self._attr_unique_id = f"{bus_stop_code}_{service_no}_{entity_description.key}"
        self.entity_id = f"sensor.sgbusarrivals_{self._attr_unique_id}"
        self._bus_stop_code = bus_stop_code
        self._service_no = service_no

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            translation_key=f"next_bus_{entity_description.cardinality}",
            translation_placeholders={
                "service_no": service_no,
                "description": description,
            },
            identifiers={
                (DOMAIN, subentry.subentry_id, entity_description.cardinality)
            },
        )

    def _get_data(self, bus_stop_code: str, service_no: str) -> BusArrival:
        if service_no in self.coordinator.data[bus_stop_code]:
            return self.coordinator.data[bus_stop_code][service_no]

        return BusArrival(
            bus_stop_code=bus_stop_code, service_no=service_no, next_bus=[]
        )

    @property
    def native_value(self) -> int:
        """Return the state of the entity."""
        bus_arrival: BusArrival = self._get_data(self._bus_stop_code, self._service_no)
        _LOGGER.debug(
            "Update sensor, bus_stop_code: %s, service_no: %s",
            self._bus_stop_code,
            self._service_no,
        )
        return self.entity_description.value_fn(
            self.entity_description.cardinality, bus_arrival
        )
