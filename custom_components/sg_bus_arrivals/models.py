"""The SG Bus Arrivals integration models."""

from dataclasses import dataclass


@dataclass
class NextBus:
    """Next bus information."""

    estimated_arrival_minutes: int | None = None
    bus_type: str | None = None
    feature: str | None = None
    load: str | None = None


@dataclass
class BusArrival:
    """Bus arrival information."""

    bus_stop_code: str
    service_no: str
    operator: str
    next_bus: list[NextBus]


@dataclass
class BusStop:
    """Class representing a bus stop."""

    bus_stop_code: str
    road_name: str
    description: str


@dataclass
class TrainServiceAlert:
    """Class representing a train service alert."""

    status: str
    messages: list[str]
