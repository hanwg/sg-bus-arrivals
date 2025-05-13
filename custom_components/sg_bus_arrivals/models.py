"""The SG Bus Arrivals integration models."""

from dataclasses import dataclass


@dataclass
class NextBus:
    """Next bus information."""

    estimated_arrival_minutes: int
    bus_type: str
    feature: str
    load: str


@dataclass
class BusArrival:
    """Bus arrival information."""

    bus_stop_code: str
    service_no: str
    next_bus: list[NextBus]


@dataclass
class BusStop:
    """Class representing a bus stop."""

    bus_stop_code: str
    road_name: str
    description: str
