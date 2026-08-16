from models.graph import Graph
from models.drone import Drone
from models.zone import Zone

ANSI: dict[str, str] = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "black":   "\033[30m",
    "red":     "\033[31m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "blue":    "\033[34m",
    "magenta": "\033[35m",
    "cyan":    "\033[36m",
    "white":   "\033[37m",
    "bg_black":   "\033[40m",
    "bg_red":     "\033[41m",
    "bg_green":   "\033[42m",
    "bg_yellow":  "\033[43m",
    "bg_blue":    "\033[44m",
    "bg_magenta": "\033[45m",
    "bg_cyan":    "\033[46m",
    "bg_white":   "\033[47m",
}

ZONE_TYPE_COLOR: dict[str, str] = {
    "normal": ANSI["blue"],
    "restricted": ANSI["red"],
    "priority": ANSI["green"],
    "blocked": ANSI["black"],
}


class TerminalVisualizer:
    """
    Renders the graph, drones, and zones in the terminal using ANSI escape codes for colors.
    """

    def __init__(self, graph: Graph, drones: list[Drone]) -> None:
        self.graph = graph
        self.drones = drones

    def print_turn_header(self, turn: int) -> None:
        """
        Prints the header for the current turn in the simulation.

        Args:
            turn (int): The current turn number.
        """
        print(
            f"\n{ANSI['bold']}{ANSI['cyan']}"
            f"{'=' * 40}"
            f"\n  TURN {turn}"
            f"\n{'=' * 40}"
            f"{ANSI['reset']}"
        )

    def print_turn_movements(self, movements: str) -> None:
        """
        Prints the movements of drones for the current turn.

        Args:
            movements (str): A string describing the movements of drones.
        """
        if not movements:
            print(f"  {ANSI['yellow']}(no movements this turn){ANSI['reset']}")
            return

        parts = []
        for token in movements.split():
            parts.append(self._colorize_movement(token))
        print("  " + " ".join(parts))

    def print_zone_states(self) -> None:
        """
        Prints the current states of all non-blocked zones in the graph.
        """
        print(f"\n{ANSI['bold']}  Zone States:{ANSI['reset']}")
        for zone in self.graph.zones.values():
            if zone.zone_type == "blocked":
                continue

            color = self._resolve_color(zone.color, zone.zone_type.value)

            drones_here = [
                d.label for d in self.drones
                if not d.delivered
                and not d.is_in_flight()
                and d.current_zone == zone
            ]
            in_flight_here = [
                d.label for d in self.drones
                if not d.delivered
                and d.is_in_flight()
                and d.current_zone == zone
            ]

            occupancy = f"{zone.current_drones}/{zone.max_drones}"
            drone_str = ""
            if drones_here:
                drone_str += f" {ANSI['green']}(-> {', '.join(in_flight_here)}){ANSI['reset']}"
            tag = ""
            if zone.is_start:
                tag = f"{ANSI['bg_green']}{ANSI['black']} START {ANSI['reset']}"
            elif zone.is_end:
                tag = f"{ANSI['bg_yellow']}{ANSI['black']} END {ANSI['reset']}"

            print(
                f"    {color}{ANSI['bold']}{zone.name:<16}{ANSI['reset']}"
                f"{color}[{zone.zone_type.value:<10}]{ANSI['reset']}"
                f"  cap: {occupancy}"
                f"{drone_str}{tag}"
            )

    def print_summary(self, total_turns: int) -> None:
        """
        Prints a summary of the simulation after all turns have been completed.

        Args:
            total_turns (int): The total number of turns taken in the simulation.
        """
        nb = len(self.drones)
        avg = total_turns / nb if nb > 0 else 0
        delivered = sum(1 for d in self.drones if d.delivered)

        print(
            f"\n{ANSI['bold']}{ANSI['green']}"
            f"{'=' * 40}"
            f"\n  SIMULATION COMPLETE"
            f"\n{'=' * 40}"
            f"{ANSI['reset']}"
        )

        print(f"  {ANSI['bold']}Total turns   :{ANSI['reset']} {total_turns}")
        print(f"  {ANSI['bold']}Drones        :{ANSI['reset']} {nb}")
        print(f"  {ANSI['bold']}Delivered     :{ANSI['reset']} {delivered}/{nb}")
        print(f"  {ANSI['bold']}Avg turns/drone:{ANSI['reset']} {avg:.1f}")

    def print_graph_overview(self) -> None:
        """
        Prints an overview of the graph, including all zones and their types.
        """
        nb_zones = len(self.graph.zones)
        nb_conn = sum(
            len(v) for v in self.graph.adjacency.values()
        ) // 2

        print(
            f"\n{ANSI['bold']}{ANSI['magenta']}"
            f"  Graph: {nb_zones} zones, {nb_conn} connections, "
            f"{self.graph.nb_drones} drones"
            f"{ANSI['reset']}"
        )
        start = self.graph.start
        end = self.graph.end
        if start and end:
            print(
                f"  Start: {ANSI['green']}{start.name}{ANSI['reset']}  "
                f"End: {ANSI['yellow']}{end.name}{ANSI['reset']}"
            )

    def _colorize_movement(self, token: str) -> str:
        """
        Colorizes a movement token based on its type.

        Args:
            token (str): The movement token to colorize.

        Returns:
            str: The colorized movement token.
        """
        if "-" not in token:
            return token
        drone_part, dest_part = token.split("-", 1)
        return (
            f"{ANSI['magenta']}{ANSI['bold']}{drone_part}{ANSI['reset']}"
            f"{ANSI['white']}-{ANSI['reset']}"
            f"{ANSI['cyan']}{dest_part}{ANSI['reset']}"
        )

    def _resolve_color(self, color: str | None, zone_type: str) -> str:
        """
        Resolves the color for a zone based on its type and any custom color.

        Args:
            color (str | None): The custom color for the zone, if any.
            zone_type (str): The type of the zone.

        Returns:
            str: The ANSI color code for the zone.
        """
        if color and color in ANSI:
            return ANSI[color]
        return ZONE_TYPE_COLOR.get(zone_type, ANSI["white"])
