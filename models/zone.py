from enum import Enum
from typing import Optional


class ZoneType(str, Enum):
    """Enum representing the type of a zone."""
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class Zone:
    """Represents a zone in the graph.

    Attributes:
        name (str): The name of the zone.
        color (Optional[str]): The color of the zone (for visualization).
        x (int): The x-coordinate of the zone.
        y (int): The y-coordinate of the zone.
        zone_type (ZoneType): The type of the zone.
        max_drones (int): The maximum number of drones allowed in the zone.
        is_start (bool): Whether this zone is a starting point for drones.
        is_end (bool): Whether this zone is an ending point for drones.
        current_drones (int): The current number of drones in the zone.
    """
    def __init__(
            self,
            name: str,
            x: int,
            y: int,
            zone_type: ZoneType = ZoneType.NORMAL,
            color: Optional[str] = None,
            max_drones: int = 1,
            is_start: bool = False,
            is_end: bool = False,
            ) -> None:
        """
        Initialize a Zone instance.

        Args:
            name (str): The name of the zone.
            x (int): The x-coordinate of the zone.
            y (int): The y-coordinate of the zone.
            zone_type (ZoneType): The type of the zone.
            color (Optional[str]): The color of the zone (for visualization).
            max_drones (int): The maximum number of drones allowed in the zone.
            is_start (bool): Whether this zone is a starting point for drones.
            is_end (bool): Whether this zone is an ending point for drones.
        """
        self.name = name
        self.color = color
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.max_drones = max_drones
        self.is_start = is_start
        self.is_end = is_end
        self.current_drones = 0

    def has_capacity(self) -> bool:
        """Check if the zone has capacity for more drones.

        Returns:
            bool: True if the zone has capacity for more drones,
                False otherwise.
        """
        if self.is_start or self.is_end:
            return True
        return self.current_drones < self.max_drones

    def movement_cost(self) -> int:
        """Return turn cost to enter this zone.

        Returns:
            int: The movement cost to enter this zone."""
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    def __repr__(self) -> str:
        """Return a string representation of the Zone instance.

        Returns:
            str: A string representation of the Zone instance.
        """
        return f"Zone({self.name}, {self.zone_type.value})"
