from typing import Optional
from zone import Zone
from connection import Connection


class Graph:
    """
    Represents a graph of zones and their connections.

    Attributes:
        zones (dict[str, Zone]): A dictionary mapping zone
            names to Zone objects.
        adjacency (dict[str, list[Connection]]): A dictionary mapping zone
            names to lists of Connection objects.
        start (Optional[Zone]): The starting zone in the graph.
        end (Optional[Zone]): The ending zone in the graph.
        nb_drones (int): The number of drones in the graph.
    """
    def __init__(self) -> None:
        """Initialize a Graph instance.
        """
        self.zones: dict[str, Zone] = {}
        self.adjacency: dict[str, list[Connection]] = {}
        self.start: Optional[Zone] = None
        self.end: Optional[Zone] = None
        self.nb_drones: int = 0

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph.

        Args:
            zone (Zone): The zone to be added to the graph.
        """
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []
        if zone.is_start:
            self.start = zone
        if zone.is_end:
            self.end = zone

    def add_connection(self, connection: Connection) -> None:
        """Register a bidirectional connection.

        Args:
            connection (Connection): The connection to be added to the graph.
        """
        self.adjacency[connection.zone_a.name].append(connection)
        self.adjacency[connection.zone_b.name].append(connection)

    def get_neighbors(self, zone: Zone) -> list[tuple[Zone, Connection]]:
        """Return all reachable neighbors with their connection.

        Args:
            zone (Zone): The zone for which to find neighbors.

        Returns:
            list[tuple[Zone, Connection]]: A list of tuples containing the
                neighbor zones and their connecting connections.
        """
        neighbors = []
        for conn in self.adjacency[zone.name]:
            neighbor = conn.other_zone(zone)
            if neighbor.zone_type != "blocked":
                neighbors.append((neighbor, conn))
        return neighbors
