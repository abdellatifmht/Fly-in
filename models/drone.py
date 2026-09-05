from models.connection import Connection
from typing import Optional
from enum import Enum
from models.zone import Zone


class DroneState(str, Enum):
    """Enum representing the state of a drone."""
    IDLE = "idle"
    MOVING = "moving"
    IN_FLIGHT = "in_flight"


class Drone:
    """Represents a single drone in the simulation.

    Attributes:
        drone_id (int): Unique identifier (e.g., 1 for D1).
        current_zone (Zone): The zone where the drone is currently located.
        target_zone (Optional[Zone]): The zone the drone is moving towards.
        path (list[Zone]): The planned path for the drone to follow.
        state (DroneState): The current state of the drone.
        flight_connection (Optional[Connection]): The connection the drone
            is currently using to move.
        flight_destination (Optional[Zone]): The zone the drone
            is flying towards.
        delivered (bool): Whether the drone has completed its delivery.
    """
    def __init__(self, drone_id: int, start_zone: Zone) -> None:
        """
        Initialize a Drone instance.

        Args:
            drone_id (int): Unique identifier for the drone.
            start_zone (Zone): The initial zone where the drone starts.
        """
        self.drone_id: int = drone_id
        self.current_zone: "Zone" = start_zone
        self.target_zone: Optional["Zone"] = None
        self.path: list["Zone"] = []
        self.state: DroneState = DroneState.IDLE
        self.flight_connection: Optional["Connection"] = None
        self.flight_destination: Optional["Zone"] = None
        self.delivered: bool = False

    @property
    def label(self) -> str:
        """Return the label of the drone (e.g., D1, D2).

        Returns:
            str: The label of the drone.
        """
        return f"D{self.drone_id}"

    def assign_path(self, path: list["Zone"]) -> None:
        """Assign a path to the drone.
        Args:
            path (list[Zone]): The list of zones representing the path.
        """
        self.path = path[1:]
        self.target_zone = self.path[-1] if self.path else None

    def next_zone(self) -> Optional["Zone"]:
        """Return the next zone in the path, if available.
        Returns:
            Optional[Zone]: The next zone in the path,
                or None if the path is empty.
        """
        return self.path[0] if self.path else None

    def advance(self) -> None:
        """Advance the drone to the next zone in its path."""
        if self.path:
            self.path.pop(0)

    def start_flight(
            self,
            connection: "Connection",
            destination_zone: "Zone",
            ) -> None:
        """Begin the first turn of a 2-turn restricted zone transit.

        Args:
            connection: The connection being traversed.
            destination: The restricted zone being approached.
        """
        self.state = DroneState.IN_FLIGHT
        self.flight_connection = connection
        self.flight_destination = destination_zone

    def complete_flight(self) -> None:
        """Complete the second turn of a 2-turn restricted zone transit."""
        if self.flight_destination:
            self.current_zone = self.flight_destination
        self.state = DroneState.IDLE
        self.flight_connection = None
        self.flight_destination = None
        self.advance()

    def move_to(self, zone: Zone) -> None:
        """Perform an immediate 1-turn move to the specified zone.

        Args:
            zone: The zone to move to.
        """
        self.current_zone = zone
        self.advance()

    def mark_delivered(self) -> None:
        """Mark the drone as having completed its delivery."""
        self.delivered = True
        self.state = DroneState.IDLE
        self.path = []

    def is_in_flight(self) -> bool:
        """Check if the drone is currently in flight."""
        return self.state == DroneState.IN_FLIGHT

    def has_a_path(self) -> bool:
        """Check if the drone has a path assigned."""
        return len(self.path) > 0

    def __repr__(self) -> str:
        """Return a string representation of the Drone instance.

        Returns:
            str: A string representation of the Drone instance.
        """
        zone_name = self.current_zone.name if self.current_zone else "None"
        if self.is_in_flight() and self.flight_destination:
            return (
                f"Drone{self.label}, "
                f"in-flight->{self.flight_destination.name}"
            )
        return f"Drone{self.label}, at={zone_name}, state={self.state.value}"
