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

    # def print_zone_states(self) -> None:
    #     """
    #     Prints the current states of all non-blocked zones in the graph.
    #     """
    #     print(f"\n{ANSI['bold']}  Zone States:{ANSI['reset']}")
    #     for zone in self.graph.zones.values():
    #         if zone.type == "blocked":
    #             continue
