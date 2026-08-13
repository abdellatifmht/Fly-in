from models.zone import Zone


class Connection:
    def __init__(
            self,
            zone_a: Zone,
            zone_b: Zone,
            max_link_capacity: int = 1,
            ) -> None:
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        self.current_usage = 0

    def has_capacity(self) -> bool:
        """Check if the connection has capacity for more drones."""
        return self.current_usage < self.max_link_capacity

    def other_zone(self, zone: Zone) -> Zone:
        """Get the other zone connected to this connection."""
        if zone == self.zone_a:
            return self.zone_b
        elif zone == self.zone_b:
            return self.zone_a
        else:
            raise ValueError("Zone is not connected to this connection.")

    def __repr__(self) -> str:
        return f"Connection({self.zone_a.name}-{self.zone_b.name})"
