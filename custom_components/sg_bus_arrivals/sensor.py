"""Platform for sensor integration."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import logging
from typing import Any

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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SgBusArrivalsConfigEntry
from .api import BUS_ARRIVALS_COUNT, SgBusArrivals
from .const import (
    DOMAIN,
    SUBENTRY_CONF_BUS_STOP_CODE,
    SUBENTRY_CONF_DESCRIPTION,
    SUBENTRY_CONF_SERVICE_NO,
    SUBENTRY_TYPE_BUS_SERVICE,
)
from .coordinator import (
    BusArrivalsUpdateCoordinator,
    SgBusArrivalsData,
    TrainServiceAlertsUpdateCoordinator,
)
from .models import BusArrival, NextBus, TrainServiceAlert

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SgBusArrivalsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""

    # retrieve our api instance
    sg_bus_arrivals_data: SgBusArrivalsData = config_entry.runtime_data
    sg_bus_arrivals: SgBusArrivals = sg_bus_arrivals_data.api
    bus_arrival_coordinator: BusArrivalsUpdateCoordinator = (
        sg_bus_arrivals_data.bus_arrivals_coordinator
    )
    train_service_alerts_coordinator: TrainServiceAlertsUpdateCoordinator = (
        sg_bus_arrivals_data.train_service_alerts_coordinator
    )

    # Fetch initial data so we have data when entities subscribe
    await bus_arrival_coordinator.async_refresh()
    await train_service_alerts_coordinator.async_refresh()

    bus_sensor_descriptions: list[SgBusArrivalsSensorDescription] = _get_sensor_descriptions(sg_bus_arrivals)

    for subentry in config_entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_TYPE_BUS_SERVICE:
            sensors: list[BusArrivalSensor] = [
                BusArrivalSensor(
                    bus_arrival_coordinator,
                    subentry,
                    sensor_description,
                    subentry.data[SUBENTRY_CONF_BUS_STOP_CODE],
                    subentry.data[SUBENTRY_CONF_DESCRIPTION],
                    subentry.data[SUBENTRY_CONF_SERVICE_NO],
                )
                for sensor_description in bus_sensor_descriptions
            ]

            async_add_entities(
                sensors, update_before_add=True, config_subentry_id=subentry.subentry_id
            )

        else:
            sensors: list[TrainServiceAlertSensor] = [
                TrainServiceAlertSensor(
                    train_service_alerts_coordinator, subentry, sensor_description
                )
                for sensor_description in _get_train_service_alerts_sensor_descriptions(
                    sg_bus_arrivals
                )
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


@dataclass(frozen=True, kw_only=True)
class TrainServiceAlertSensorDescription(SensorEntityDescription):
    """Describes the train service alert sensor entity."""

    line: str
    value_fn: Callable[[str, dict[str, TrainServiceAlert]], str]


def _get_train_service_alerts_sensor_descriptions(
    sg_bus_arrivals: SgBusArrivals,
) -> list[TrainServiceAlertSensorDescription]:
    lines: list[str] = sg_bus_arrivals.get_train_lines()
    train_statuses: list[str] = sg_bus_arrivals.get_train_statuses()
    return [
        TrainServiceAlertSensorDescription(
            key=f"train_service_alerts_{line}",
            line=line,
            device_class=SensorDeviceClass.ENUM,
            options=train_statuses,
            value_fn=lambda line, alerts: alerts[line],
            translation_key=f"train_service_alerts_{line}",
        )
        for line in lines
    ]


def _get_sensor_descriptions(sg_bus_arrivals: SgBusArrivals) -> list[SgBusArrivalsSensorDescription]:
    sensor_descriptions = []

    sensor_descriptions.append(
        SgBusArrivalsSensorDescription(
            cardinality=0,
            key="next_bus_estimated_arrivals",
            value_fn=lambda cardinality, bus_arrival: " / ".join(
                [
                    str(next_bus.estimated_arrival_minutes)
                    if next_bus.estimated_arrival_minutes
                    else "-"
                    for next_bus in bus_arrival.next_bus
                ]
            ),
            translation_key="next_bus_estimated_arrival",
        )
    )

    bus_types: list[str] = sg_bus_arrivals.get_bus_types()
    features: list[str] = sg_bus_arrivals.get_features()
    bus_loads: list[str] = sg_bus_arrivals.get_bus_loads()

    for i in range(1, BUS_ARRIVALS_COUNT + 1):
        sensor_descriptions.append(
            SgBusArrivalsSensorDescription(
                cardinality=i,
                key=f"next_bus_{i}_estimated_arrival",
                native_unit_of_measurement=UnitOfTime.MINUTES,
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda cardinality, bus_arrival: bus_arrival.next_bus[
                    cardinality - 1
                ].estimated_arrival_minutes,
                translation_key="next_bus_estimated_arrival",
            )
        )

        sensor_descriptions.append(
            SgBusArrivalsSensorDescription(
                cardinality=i,
                key=f"next_bus_{i}_bus_type",
                device_class=SensorDeviceClass.ENUM,
                options=bus_types,
                value_fn=lambda cardinality, bus_arrival: bus_arrival.next_bus[
                    cardinality - 1
                ].bus_type,
                translation_key="next_bus_bus_type",
            )
        )

        sensor_descriptions.append(
            SgBusArrivalsSensorDescription(
                cardinality=i,
                key=f"next_bus_{i}_feature",
                device_class=SensorDeviceClass.ENUM,
                options=features,
                value_fn=lambda cardinality, bus_arrival: bus_arrival.next_bus[
                    cardinality - 1
                ].feature,
                translation_key="next_bus_feature",
            )
        )

        sensor_descriptions.append(
            SgBusArrivalsSensorDescription(
                cardinality=i,
                key=f"next_bus_{i}_load",
                device_class=SensorDeviceClass.ENUM,
                options=bus_loads,
                value_fn=lambda cardinality, bus_arrival: bus_arrival.next_bus[
                    cardinality - 1
                ].load,
                translation_key="next_bus_load",
            )
        )

    return sensor_descriptions


class TrainServiceAlertSensor(
    CoordinatorEntity[TrainServiceAlertsUpdateCoordinator], SensorEntity
):
    """Sensor tracking train service alerts."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrainServiceAlertsUpdateCoordinator,
        subentry: ConfigSubentry,
        entity_description: TrainServiceAlertSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"train_service_alert_{entity_description.line}"
        self.entity_id = (
            f"sensor.sgbusarrivals_train_service_alert_{entity_description.line}"
        )

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            translation_key="train_service_alerts",
            identifiers={(DOMAIN, subentry.subentry_id)},
        )

    def _get_data(self):
        line: str = self.entity_description.line
        alerts: dict[str, TrainServiceAlert] = self.coordinator.data
        return self.entity_description.value_fn(line, alerts)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the extra state attributes."""

        attrs: Mapping[str, Any] = {}
        attrs["messages"] = self._get_data().messages
        return attrs

    @property
    def native_value(self) -> str:
        """Return the state of the entity."""
        return self._get_data().status


class BusArrivalSensor(CoordinatorEntity[BusArrivalsUpdateCoordinator], SensorEntity):
    """Sensor tracking the number of minutes till bus arrival."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BusArrivalsUpdateCoordinator,
        subentry: ConfigSubentry,
        entity_description: SgBusArrivalsSensorDescription,
        bus_stop_code: str,
        description: str,
        service_no: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
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

    @property
    def native_value(self) -> int:
        """Return the state of the entity."""
        bus_arrival: BusArrival = (
            self.coordinator.data[self._bus_stop_code][self._service_no]
            if self._bus_stop_code in self.coordinator.data
            and self._service_no in self.coordinator.data[self._bus_stop_code]
            else BusArrival(
                self._bus_stop_code,
                self._service_no,
                [
                    NextBus(None, None, None, None)
                    for i in range(1, BUS_ARRIVALS_COUNT + 1)
                ],
            )
        )
        return self.entity_description.value_fn(
            self.entity_description.cardinality, bus_arrival
        )
