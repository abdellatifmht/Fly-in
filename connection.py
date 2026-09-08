from zone import Zone


class Connection:
    """
    Represents a connection between two zones.

    Attributes:
        zone_a (Zone): One end of the connection.
        zone_b (Zone): The other end of the connection.
        max_link_capacity (int): The maximum number of drones that can
            use this connection simultaneously.
        current_usage (int): The current number of drones using this
            connection.
    """
    def __init__(
            self,
            zone_a: Zone,
            zone_b: Zone,
            max_link_capacity: int = 1,
            ) -> None:
        """
        Initialize a Connection instance.

        Args:
            zone_a (Zone): One end of the connection.
            zone_b (Zone): The other end of the connection.
            max_link_capacity (int): The maximum number of drones that can
                use this connection simultaneously.
        """
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity
        self.current_usage = 0

    def has_capacity(self) -> bool:
        """
        Check if the connection has available capacity for more traffic.

        Returns:
            bool: True if the connection has available capacity,
                False otherwise.
        """
        return self.current_usage < self.max_link_capacity

    def other_zone(self, zone: Zone) -> Zone:
        """
        Get the other zone connected to this connection.

        Args:
            zone (Zone): One of the zones connected to this connection.

        Returns:
            Zone: The other zone connected to this connection.

        Raises:
            ValueError: If the provided zone is not connected to this
                connection.
        """
        if zone == self.zone_a:
            return self.zone_b
        elif zone == self.zone_b:
            return self.zone_a
        else:
            raise ValueError("Zone is not connected to this connection.")

    def __repr__(self) -> str:
        """
        Return a string representation of the Connection instance.

        Returns:
            str: A string representation of the Connection instance.
        """
        return f"Connection({self.zone_a.name}-{self.zone_b.name})"
