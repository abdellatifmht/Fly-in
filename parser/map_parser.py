import re
from typing import Optional
from models.zone import Zone, ZoneType
from models.graph import Graph
from models.connection import Connection


class ParserError(Exception):
    """Custom exception for parser errors."""
    pass


class MapParser:
    def parse(self, filepath: str) -> Graph:
        """Parse the map file and return a Graph object."""
        graph = Graph()
        seen_connections: set[frozenset[str]] = set()

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except OSError as e:
            raise ParserError(f"Error reading file: {e}")

        first_instruction_found = False

        for index, line in enumerate(lines, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if not first_instruction_found:
                if line.startswith("nb_drones"):
                    first_instruction_found = True
                else:
                    raise ParserError(f"Line {index}: The first instruction must be 'nb_drones'.")
            try:
                self._parse_line(line, index, graph, seen_connections)
            except ParserError as e:
                raise ParserError(f"Line {index}: {e}")
            except Exception as e:
                raise ParserError(f"Line {index}: Unexpected error: {e}")

        self._validate_graph(graph)
        return graph

    def _parse_line(
            self,
            line: str,
            line_number: int,
            graph: Graph,
            seen_connections: set[frozenset[str]]
            ) -> None:
        """Parse a single line and update the graph."""

        if line.startswith("nb_drones"):
            self._parse_nb_drones(line, line_number, graph)
        elif line.startswith("start_hub"):
            self._parse_zone(line, line_number, graph, is_start=True)
        elif line.startswith("end_hub"):
            self._parse_zone(line, line_number, graph, is_end=True)
        elif line.startswith("hub"):
            self._parse_zone(line, line_number, graph)
        elif line.startswith("connection"):
            self._parse_connection(line, line_number, graph, seen_connections)
        else:
            raise ParserError(f"Line {line_number}: Unknown line type. Expected 'nb_drones', 'start_hub', 'end_hub', 'hub', or 'connection'.")

    def _parse_nb_drones(self, line: str, line_number: int, graph: Graph) -> None:
        """Parse the number of drones."""
        match = re.match(r"nb_drones:\s*(\d+)$", line)
        if not match:
            raise ParserError(f"Line {line_number}: {line} is not a valid nb_drones declaration. Expected format: 'nb_drones: <number>'.")
        if int(match.group(1)) < 1:
            raise ParserError(f"Line {line_number}: {line} is not a valid nb_drones declaration. Number of drones must be a positive integer.")
        graph.nb_drones = int(match.group(1))

    def _parse_zone(
            self,
            line: str,
            line_number: int,
            graph: Graph,
            is_start: bool = False,
            is_end: bool = False
            ) -> None:
        pattern = r"(?:start_hub|end_hub|hub):\s+(\S+)\s+(-?\d+)\s+(-?\d+)(?:\s+\[([^\]]*)\])?"
        match = re.match(pattern, line)
        if not match:
            raise ParserError(f"Line {line_number}: Invalid zone format. Expected 'hub: <name> <x> <y> [<metadata>]'.")
        name, x, y = match.group(1), int(match.group(2)), int(match.group(3))
        metadata = match.group(4) or ""

        if "-" in name:
            raise ParserError(f"Line {line_number}: Zone name cannot contain '-' character.")

        zone_type, color, max_drones = self._parse_metadata(metadata, line_number)
        zone = Zone(name, x, y, zone_type, color, max_drones, is_start=is_start, is_end=is_end)
        graph.add_zone(zone)

    def _parse_metadata(
            self,
            metadata: str,
            line_number: int
            ) -> tuple[ZoneType, Optional[str], int]:
        """Parse the metadata for a zone."""
        zone_type = ZoneType.NORMAL
        color = None
        max_drones = 1

        for item in metadata.split():
            if item.startswith("zone="):
                value = item.split("=")[1]
                try:
                    zone_type = ZoneType(value)
                except ValueError:
                    raise ParserError(f"Line {line_number}: Invalid zone type '{value}'. Must be one of {[z.value for z in ZoneType]}.")
            elif item.startswith("color="):
                color = item.split("=")[1]
            elif item.startswith("max_drones="):
                try:
                    max_drones = int(item.split("=")[1])
                    if max_drones < 1:
                        raise ValueError
                except ValueError:
                    raise ParserError(f"Line {line_number}: Invalid max_drones value. Must be a positive integer.")
        return zone_type, color, max_drones

    def _parse_connection(
            self,
            line: str,
            line_number: int,
            graph: Graph,
            seen_connections: set[frozenset[str]]
            ) -> None:
        """Parse a connection line and update the graph."""
        match = re.match(r"connection:\s+(\S+)-(\S+)(?:\s+\[([^\]]*)\])?", line)
        if not match:
            raise ParserError(f"Line {line_number}: Invalid connection format. Expected 'connection: <zone_a>-<zone_b> [<metadata>]'")
        zone_a_name, zone_b_name = match.group(1), match.group(2)
        metadata = match.group(3) or ""

        if zone_a_name not in graph.zones:
            raise ParserError(f"Line {line_number}: Zone '{zone_a_name}' is not defined.")
        if zone_b_name not in graph.zones:
            raise ParserError(f"Line {line_number}: Zone '{zone_b_name}' is not defined.")

        connection_key = frozenset([zone_a_name, zone_b_name])
        if connection_key in seen_connections:
            raise ParserError(f"Line {line_number}: Duplicate connection between '{zone_a_name}' and '{zone_b_name}'.")
        seen_connections.add(connection_key)

        max_link_capacity = 1
        for item in metadata.split():
            if item.startswith("max_link_capacity="):
                try:
                    max_link_capacity = int(item.split("=")[1])
                    if max_link_capacity < 1:
                        raise ValueError
                except ValueError:
                    raise ParserError(f"Line {line_number}: Invalid max_link_capacity value. Must be a positive integer.")

        connection = Connection(graph.zones[zone_a_name], graph.zones[zone_b_name], max_link_capacity)
        graph.add_connection(connection)

    def _validate_graph(self, graph: Graph) -> None:
        """Validate the graph after parsing."""
        if graph.start is None:
            raise ParserError("No start hub defined in the map.")
        if graph.end is None:
            raise ParserError("No end hub defined in the map.")
        if graph.nb_drones == 0:
            raise ParserError("Missing nb_drones declaration.")
