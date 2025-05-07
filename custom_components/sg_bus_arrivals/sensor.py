"""Platform for sensor integration."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SgBusArrivalsConfigEntry
from .const import OPTIONS_BUS_STOP_CODE
from .sg_bus_arrivals_service import SgBusArrivalsService


# See cover.py for more details.
# Note how both entities for each roller sensor (battery and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SgBusArrivalsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""

    # retrieve our api instance
    service: SgBusArrivalsService = config_entry.runtime_data

    # retrieve configuration
    bus_stop_code: str = config_entry.options[OPTIONS_BUS_STOP_CODE]

    new_sensors = []
    # for roller in hub.rollers:
    #    new_devices.append(BatterySensor(roller))
    #    new_devices.append(IlluminanceSensor(roller))
    # new_sensors.append(BusArrivalSensor(bus_stop_code))
    if new_sensors:
        async_add_entities(new_sensors)


class BusArrivalSensor(SensorEntity):
    """Sensor tracking the number of minutes till bus arrival."""

    def __init__(self, description: str, bus_stop_code: str, service_no: str) -> None:
        """Initialize the sensor."""
        self._description = description
        self._bus_stop_code = bus_stop_code
        self._service_no = service_no
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_unique_id = f"{bus_stop_code}_{service_no}"
        self._attr_name = description
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_value = None
