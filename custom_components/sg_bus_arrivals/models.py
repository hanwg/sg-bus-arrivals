"""The SG Bus Arrivals integration models."""

from dataclasses import dataclass


@dataclass
class BusArrival:
    """Bus arrival information."""

    def __init__(
        self,
        bus_stop_code: str,
        service_no: str,
        next_bus_minutes: int,
        next_bus_minutes_2: int,
        next_bus_minutes_3: int,
    ) -> None:
        """Initialize bus arrival."""
        self.bus_stop_code = bus_stop_code
        self.service_no = service_no
        self.next_bus_minutes = next_bus_minutes
        self.next_bus_minutes_2 = next_bus_minutes_2
        self.next_bus_minutes_3 = next_bus_minutes_3


@dataclass
class BusStop:
    """Class representing a bus stop."""

    def __init__(self, bus_stop_code: str, road_name: str, description: str) -> None:
        """Initialize the bus stop."""
        self.bus_stop_code = bus_stop_code
        self.road_name = road_name
        self.description = description
