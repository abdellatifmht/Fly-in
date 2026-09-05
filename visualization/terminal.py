import sys
from models.graph import Graph
from models.drone import Drone

try:
    from webcolors import name_to_hex
except (ImportError, ModuleNotFoundError):
    print("moduele webcolors not installed!")
    sys.exit(1)

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

ZONE_TYPE_HEX: dict[str, str] = {
    "normal":     "#3498db",
    "restricted": "#e74c3c",
    "priority":   "#2ecc71",
    "blocked":    "#7f8c8d",
}


def hex_to_ansi(hex_c: str) -> str:
    """Convert hex color (#rrggbb) to ANSI 24-bit foreground code."""
    h = hex_c.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


class TerminalVisualizer:
    """Renders the simulation using ANSI escape codes.

    Attributes:
        graph:  The zone graph.
        drones: All drones in the simulation.
    """

    def __init__(self, graph: Graph, drones: list[Drone]) -> None:
        self.graph = graph
        self.drones = drones

    def _resolve_ansi(self, color: str | None, fallback: str) -> str:
        """Resolve a color string to an ANSI escape code.

        Args:
            color:    Hex string or CSS3 name, or None.
            fallback: Hex fallback if color is None or invalid.

        Returns:
            ANSI foreground escape code.
        """
        if not color:
            return hex_to_ansi(fallback)
        hex_c = color if color.startswith("#") else ""
        if not hex_c:
            try:
                hex_c = name_to_hex(color)
            except (ValueError, AttributeError):
                hex_c = fallback
        return hex_to_ansi(hex_c)

    def _zone_ansi(self, zone_name: str) -> str:
        """Return ANSI color code for a zone.

        Args:
            zone_name: Name of the zone.

        Returns:
            ANSI escape code string.
        """
        zone = self.graph.zones.get(zone_name)
        if zone is None:
            return ""
        fallback = ZONE_TYPE_HEX.get(zone.zone_type.value, "#ffffff")
        return self._resolve_ansi(zone.color, fallback)

    def _colored_zone_name(self, zone_name: str) -> str:
        """Return colored zone name string.

        Args:
            zone_name: Name of the zone.

        Returns:
            ANSI-colored zone name followed by reset.
        """
        return f"{self._zone_ansi(zone_name)}{zone_name}{RESET}"

    def print_graph_overview(self) -> None:
        """Print a colored overview of the graph at startup."""
        start = self.graph.start
        end = self.graph.end
        nb_zones = len(self.graph.zones)
        nb_conn = sum(len(v) for v in self.graph.adjacency.values()) // 2
        print(f"\n{BOLD}=== FLY-IN SIMULATION ==={RESET}")
        print(f"  Zones: {nb_zones}  Connections: {nb_conn}  Drones: {self.graph.nb_drones}")
        print(f"  Start : {self._colored_zone_name(start.name) if start else 'None'}")
        print(f"  End   : {self._colored_zone_name(end.name) if end else 'None'}\n")

    def print_turn_header(self, turn: int) -> None:
        """Print a turn separator.

        Args:
            turn: Current turn number.
        """
        print(f"\n{BOLD}--- Turn {turn} ---{RESET}")

    def print_turn_movements(self, movements: str) -> None:
        """Print drone movements with zone colors.

        Args:
            movements: Space-separated movement string.
        """
        if not movements:
            print(f"  {DIM}(no movements){RESET}")
            return

        parts: list[str] = []
        for token in movements.split():
            if "-" not in token:
                parts.append(token)
                continue
            drone_part, dest_part = token.split("-", 1)
            # connexion en vol (zoneA-zoneB)
            if self.graph.zones.get(dest_part) is None and "-" in dest_part:
                a, b = dest_part.split("-", 1)
                dest_colored = f"{self._colored_zone_name(a)}->{self._colored_zone_name(b)}"
            else:
                dest_colored = self._colored_zone_name(dest_part)
            parts.append(f"{BOLD}\033[35m{drone_part}{RESET}-{dest_colored}")

        print("  " + "  ".join(parts))

    def print_zone_states(self) -> None:
        """Print occupancy state for each zone."""
        print("")
        for zone in self.graph.zones.values():
            drones_here = [
                d.label for d in self.drones
                if not d.delivered and not d.is_in_flight()
                and d.current_zone == zone
            ]
            in_flight = [
                d.label for d in self.drones
                if d.is_in_flight() and d.flight_destination == zone
            ]
            tag = " [START]" if zone.is_start else " [END]" if zone.is_end else ""
            drone_str = f"  {' '.join(drones_here)}" if drones_here else ""
            flight_str = f"  (→ {' '.join(in_flight)})" if in_flight else ""
            pad = " " * max(0, 20 - len(zone.name))
            print(
                f"  {self._colored_zone_name(zone.name)}{pad}"
                f"{DIM}{zone.zone_type.value:<12}{RESET}"
                f"cap: {zone.current_drones}/{zone.max_drones}"
                f"{drone_str}{flight_str}{tag}"
            )
        print("")

    def print_summary(self, total_turns: int) -> None:
        """Print final simulation summary.

        Args:
            total_turns: Total number of turns used.
        """
        print(f"\n{BOLD}=== SIMULATION COMPLETE ==={RESET}")
        nb = len(self.drones)
        delivered = sum(1 for d in self.drones if d.delivered)
        end = self.graph.end
        print(f"  Delivered    : {delivered}")
        print(f"  Delivered to : {self._colored_zone_name(end.name) if end else 'goal'}")
        print(f"  Total turns  : {total_turns}")
