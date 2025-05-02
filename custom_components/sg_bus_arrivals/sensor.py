"""Platform for sensor integration."""

# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import random

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import LIGHT_LUX, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SgBusArrivalsConfigEntry
from .const import DOMAIN


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
    # hub = config_entry.runtime_data

    new_devices = []
    # for roller in hub.rollers:
    #    new_devices.append(BatterySensor(roller))
    #    new_devices.append(IlluminanceSensor(roller))
    # new_devices.append(SensorBase())
    if new_devices:
        async_add_entities(new_devices)


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.
class SensorBase(Entity):
    """Base representation of a Hello World Sensor."""

    def __init__(self):
        #    """Initialize the sensor."""
        #    self._roller = roller
        self._attr_unique_id = "sg_bus_arrivals_api"
        self._attr_name = "LTA DataMall API"
