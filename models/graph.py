from typing import Optional
from models.zone import Zone
from models.connection import Connection


class Graph:
    def __init__(self) -> None:
        self.zones: dict[str, Zone] = {}
        self.adjacency: dict[str, list[Connection]] = {}
        self.start: Optional[Zone] = None
        self.end: Optional[Zone] = None
        self.nb_drones: int = 0

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph."""
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []
        if zone.is_start:
            self.start = zone
        if zone.is_end:
            self.end = zone

    def add_connection(self, connection: Connection) -> None:
        """Register a bidirectional connection."""
        self.adjacency[connection.zone_a.name].append(connection)
        self.adjacency[connection.zone_b.name].append(connection)

    def get_neighbors(self, zone: Zone) -> list[tuple[Zone, Connection]]:
        """Return all reachable neighbors with their connection."""
        neighbors = []
        for conn in self.adjacency[zone.name]:
            neighbor = conn.other_zone(zone)
            if neighbor.zone_type != "blocked":
                neighbors.append((neighbor, conn))
        return neighbors
