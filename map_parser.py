import re
import sys
from typing import Optional
from zone import Zone, ZoneType
from graph import Graph
from connection import Connection

try:
    from webcolors import name_to_hex
except (ImportError, ModuleNotFoundError):
    print("moduele webcolors not installed!")
    sys.exit(1)


class ParserError(Exception):
    """Custom exception for parser errors."""
    pass


class MapParser:
    """Parser for the map file format."""
    VALID_META_DATA = {"zone", "color", "max_drones"}
    VALID_CONNECTION_META_DATA = {"max_link_capacity"}

    def parse(self, filepath: str) -> Graph:
        """
        Parse the map file and return a Graph object.

        Args:
            filepath (str): The path to the map file.

        Returns:
            Graph: The parsed graph object.

        Raises:
            ParserError: If there are any errors in the map file.
        """
        graph = Graph()
        seen_connections: set[frozenset[str]] = set()
        seen_coordinates: set[tuple[int, int]] = set()

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except OSError as e:
            raise ParserError(f"Error reading file: {e}")

        first_instruction_found = False

        if not lines or all(line.strip() == "" for line in lines):
            raise ParserError("The map file is empty.")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if not first_instruction_found:
                if line.startswith("nb_drones"):
                    first_instruction_found = True
                else:
                    raise ParserError(
                        f"Line: {line}.\n"
                        f"The first line must be'nb_drones'."
                        )
            if line.startswith("start_hub") and graph.start is not None:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Multiple start hubs defined."
                )
            if line.startswith("end_hub") and graph.end is not None:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Multiple end hubs defined."
                )
            try:
                self._parse_line(
                    line,
                    graph,
                    seen_connections,
                    seen_coordinates
                    )
            except ParserError as e:
                raise ParserError(e)
            except Exception as e:
                raise ParserError(f"Line:{line}\n"
                                  f"Unexpected error: {e}")

        self._validate_graph(graph)
        return graph

    def _parse_line(
            self,
            line: str,
            graph: Graph,
            seen_connections: set[frozenset[str]],
            seen_coordinates: set[tuple[int, int]],
            ) -> None:
        """
        Parse a single line and update the graph.

        Args:
            line (str): The line to parse.
            graph (Graph): The graph to update.
            seen_connections (set): A set to check for duplicates.
            seen_coordinates (set): A set to check for duplicate coordinates.

        Raises:
            ParserError: If the line is invalid or contains errors.
        """

        if line.startswith("nb_drones"):
            self._parse_nb_drones(line, graph)
        elif line.startswith("start_hub"):
            self._parse_zone(line, graph, seen_coordinates, is_start=True)
        elif line.startswith("end_hub"):
            self._parse_zone(line, graph, seen_coordinates, is_end=True)
        elif line.startswith("hub"):
            self._parse_zone(line, graph, seen_coordinates)
        elif line.startswith("connection"):
            self._parse_connection(line, graph, seen_connections)
        else:
            raise ParserError(f"Line:{line}\n"
                              f"Unknown line type.")

    def _parse_nb_drones(self, line: str, graph: Graph) -> None:
        """
        Parse the number of drones.

        Args:
            line (str): The line containing the number of drones.
            graph (Graph): The graph to update.

        Raises:
            ParserError: If the line is invalid or contains errors.
        """
        match = re.match(r"nb_drones:\s*(\d+)$", line)
        if not match:
            raise ParserError(
                f"Line:{line}\n"
                f"Invalid nb_drones declaration."
                f" Expected format: 'nb_drones: <number>'."
            )
        if int(match.group(1)) < 1:
            raise ParserError(
                f"Line:{line}\n"
                f"Invalid nb_drones declaration."
                f" Number of drones must be a positive integer."
            )
        graph.nb_drones = int(match.group(1))

    def _parse_zone(
            self,
            line: str,
            graph: Graph,
            seen_coordinates: set[tuple[int, int]],
            is_start: bool = False,
            is_end: bool = False,
            ) -> None:
        """
        Parse a zone line and update the graph.

        Args:
            line (str): The line containing the zone information.
            graph (Graph): The graph to update.
            is_start (bool): Whether this zone is a start hub.
            is_end (bool): Whether this zone is an end hub.

        Raises:
            ParserError: If the line is invalid or contains errors.
        """
        pattern = r"""
            (?:start_hub|end_hub|hub):
            \s+(\S+)
            \s+(-?\d+)
            \s+(-?\d+)
            (?:\s+\[([^\]]*)\])?
            \s*$
        """
        match = re.match(pattern, line, re.VERBOSE)
        if not match:
            raise ParserError(
                f"Line:{line}\n"
                f"Invalid zone format."
                f" Expected 'hub: <name> <x> <y> [<metadata>]'."
            )
        name = match.group(1)
        try:
            x = int(match.group(2))
            y = int(match.group(3))
        except ValueError:
            raise ParserError(
                f"Line:{line}\n"
                f"Invalid coordinates for zone '{name}'."
            )
        coordinate = (x, y)
        if coordinate in seen_coordinates:
            raise ParserError(
                f"Line:{line}\n"
                f"Duplicate coordinates ({x}, {y}) for zone '{name}'."
            )
        seen_coordinates.add(coordinate)
        if name in graph.zones:
            raise ParserError(
                f"Line:{line}\n"
                f"Zone name '{name}' is already defined."
            )
        metadata = match.group(4)
        if metadata is not None and not metadata.strip():
            raise ParserError(
                f"Line:{line}\n"
                f"Metadata cannot be empty."
            )
        metadata = metadata or ""
        if "-" in name:
            raise ParserError(
                f"Line:{line}\n"
                f"Zone name cannot contain '-' character."
            )

        zone_type, color, max_drones = self._parse_metadata(metadata, line)
        zone = Zone(name, x, y, zone_type, color, max_drones, is_start, is_end)
        graph.add_zone(zone)

    def _parse_metadata(
            self,
            metadata: str,
            line: str
            ) -> tuple[ZoneType, Optional[str], int]:
        """Parse the metadata for a zone.
        Args:
            metadata (str): The metadata string to parse.
            line (str): The line containing the metadata.

        Returns:
            tuple[ZoneType, Optional[str], int]: A tuple containing the
                zone type, color, and maximum number of drones.
        """
        zone_type = ZoneType.NORMAL
        color = None
        seen_items = set()
        max_drones = 1

        for token in metadata.split():
            if token.count("=") != 1:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Invalid metadata format '{token}'."
                    f" Expected format: 'key=value'."
                )

            item, value = token.split("=")

            if item not in self.VALID_META_DATA:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Invalid metadata item '{item}'."
                )
            if item in seen_items:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Duplicate metadata item '{item}'."
                )
            seen_items.add(item)
            if item == "zone":
                value = value.lower()
                try:
                    zone_type = ZoneType(value)
                except ValueError:
                    raise ParserError(
                        f"Line:{line}\n"
                        f"Invalid zone type '{value}'."
                    )
            elif item == "color":
                try:
                    color = name_to_hex(value)
                except ValueError:
                    raise ParserError(
                        f"Line:{line}\n"
                        f"Invalid color name '{value}'."
                    )
            elif item == "max_drones":
                try:
                    max_drones = int(value)
                    if max_drones < 1:
                        raise ValueError
                except ValueError:
                    raise ParserError(
                        f"Line:{line}\n"
                        f"max_drones value must be a positive integer."
                    )
        return zone_type, color, max_drones

    def _parse_connection(
            self,
            line: str,
            graph: Graph,
            seen_connections: set[frozenset[str]]
            ) -> None:
        """
        Parse a connection line and update the graph.

        Args:
            line (str): The line containing the connection information.
            graph (Graph): The graph to update.
            seen_connections (set): A set to check for duplicate connections.

        Raises:
            ParserError: If the line is invalid or contains errors.
        """
        match = re.match(
            r"connection:\s+(\S+)-(\S+)(?:\s+\[([^\]]*)\])?\s*$",
            line
            )
        if not match:
            raise ParserError(
                f"Line:{line}\n"
                f"Invalid connection format."
                f" Expected 'connection: <zone_a>-<zone_b> [<metadata>]'"
            )
        zone_a_name, zone_b_name = match.group(1), match.group(2)
        if zone_a_name == zone_b_name:
            raise ParserError(
                f"Line:{line}\n"
                f"Connection cannot be made between the same zone."
            )
        metadata = match.group(3)
        if metadata is not None and not metadata.strip():
            raise ParserError(
                f"Line:{line}\n"
                f"Metadata cannot be empty."
            )
        metadata = metadata or ""
        max_link_capacity = self._parse_connection_metadata(metadata, line)
        if zone_a_name not in graph.zones:
            raise ParserError(
                f"Line:{line}\n"
                f"Zone '{zone_a_name}' is not defined."
            )
        if zone_b_name not in graph.zones:
            raise ParserError(
                f"Line:{line}\n"
                f"Zone '{zone_b_name}' is not defined."
            )

        connection_key = frozenset([zone_a_name, zone_b_name])
        if connection_key in seen_connections:
            raise ParserError(
                f"Line:{line}\n"
                f"Duplicate connection between "
                f"'{zone_a_name}' and '{zone_b_name}'."
            )
        seen_connections.add(connection_key)

        connection = Connection(
            graph.zones[zone_a_name],
            graph.zones[zone_b_name],
            max_link_capacity
            )
        graph.add_connection(connection)

    def _parse_connection_metadata(
            self,
            metadata: str,
            line: str
            ) -> int:
        """
        Parse the metadata for a connection.

        Args:
            metadata (str): The metadata string to parse.
            line (str): The line number for error reporting.

        Returns:
            int: The max_link_capacity value.

        Raises:
            ParserError: If the metadata is invalid or contains errors.
        """
        seen_items = set()
        max_link_capacity = 1
        for token in metadata.split():
            if token.count("=") != 1:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Invalid metadata format '{token}'."
                    f" Expected format: 'key=value'."
                )
            item = token.split("=")[0]
            if item not in self.VALID_CONNECTION_META_DATA:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Invalid connection metadata item '{item}'."
                )
            if item in seen_items:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Duplicate connection metadata item '{item}'."
                    f" Each item can only be specified once."
                )
            seen_items.add(item)

            if token.startswith("max_link_capacity="):
                try:
                    max_link_capacity = int(token.split("=")[1])
                    if max_link_capacity < 1:
                        raise ValueError
                except ValueError:
                    raise ParserError(
                        f"Line:{line}\n"
                        f"Invalid max_link_capacity value. "
                        f"Must be a positive integer."
                    )
            else:
                raise ParserError(
                    f"Line:{line}\n"
                    f"Unknown connection metadata item '{item}'."
                )
        return max_link_capacity

    def _validate_graph(self, graph: Graph) -> None:
        """
        Validate the graph after parsing.

        Args:
            graph (Graph): The graph to validate.

        Raises:
            ParserError: If the graph is invalid.
        """
        if graph.start is None:
            raise ParserError("No start hub defined in the map.")
        if graph.end is None:
            raise ParserError("No end hub defined in the map.")
        if graph.nb_drones == 0:
            raise ParserError("Missing nb_drones declaration.")
