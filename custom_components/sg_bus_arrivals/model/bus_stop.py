"""Class representing a bus stop."""


class BusStop:
    """Class representing a bus stop."""

    def __init__(self, bus_stop_code: str, road_name: str, description: str) -> None:
        """Initialize the bus stop."""
        self.bus_stop_code = bus_stop_code
        self.road_name = road_name
        self.description = description
