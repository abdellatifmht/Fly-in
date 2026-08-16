from typing import Optional
from models.drone import Drone
from models.zone import Zone, ZoneType
from models.connection import Connection
from models.graph import Graph
from pathfinding import Dijkstra
from visualization.terminal import TerminalVisualizer


class SimulationEngine:
    """Runs the turn-by-turn drone routing simulation.

    Attributes:
        graph:   The zone graph.
        drones:  All drones participating in the simulation.
        dijkstra: Pathfinder instance.
        turn:    Current simulation turn number.
        log:     List of output lines (one per turn).
    """

    def __init__(self, graph: Graph) -> None:
        """Initializes the simulation engine.

        Args:
            graph: The zone graph.
        """
        self.graph = graph
        self.drones: list[Drone] = []
        self.dijkstra = Dijkstra(graph)
        self.turn: int = 0
        self.log: list[str] = []
        self.visualizer: TerminalVisualizer | None = None

    def setup(self, visual: bool = True) -> None:
        """Creates drones and assign initial paths."""
        if self.graph.start is None or self.graph.end is None:
            raise RuntimeError("Start and end zones must be defined in the graph.")

        paths = self.dijkstra.find_all_paths(
            self.graph.start,
            self.graph.end,
            max_paths=self.graph.nb_drones,
            )

        if not paths:
            raise RuntimeError("No paths found from start to end zone.")

        for i in range(1, self.graph.nb_drones + 1):
            drone = Drone(i, self.graph.start)
            path = paths[(i - 1) % len(paths)]
            drone.assign_path(path)
            self.drones.append(drone)

        self.graph.start.current_drones = self.graph.nb_drones

        if visual:
            self.visualizer = TerminalVisualizer(self.graph, self.drones)
            self.visualizer.print_graph_overview()

    def run(self, visual: bool = True) -> int:
        """Run the full simulation until all drones are delivered.

        Returns:
            The total number of turns used.
        """
        self.setup(visual)
        while not self._all_delivered():
            self.turn += 1
            turn_output = self._run_turn()
            if turn_output:
                self.log.append(turn_output)

            if self.visualizer:
                self.visualizer.print_turn_header(self.turn)
                self.visualizer.print_turn_movements(turn_output)
                self.visualizer.print_zone_states()

        if self.visualizer:
            self.visualizer.print_summary(self.turn)
        return self.turn

    def _all_delivered(self) -> bool:
        """Check if all drones have completed their deliveries.

        Returns:
            True if all drones are delivered, False otherwise.
        """
        return all(drone.delivered for drone in self.drones)

    def _run_turn(self) -> str:
        """Execute one simulation turn.

        Returns:
            A string representing the output for the current turn.
        """
        intentions: dict[int, Optional[tuple[str, Zone, Optional[Connection]]]] = {}

        for drone in self.drones:
            if drone.delivered:
                intentions[drone.drone_id] = None
                continue
            intentions[drone.drone_id] = self._decide(drone)

        validated = self._resolve_conflicts(intentions)

        movements: list[str] = []

        for drone in self.drones:
            if drone.delivered:
                continue

            action = validated.get(drone.drone_id)
            if action is None:
                continue

            action_type, target_zone, conn = action

            if action_type == "flight_complete":
                self._free_zone(drone.current_zone, drone)
                drone.complete_flight()
                self._occupy_zone(target_zone, drone)
                if conn:
                    conn.current_usage -= 1
                movements.append(f"{drone.label}-{target_zone.name}")

            elif action_type == "flight_start":
                self._free_zone(drone.current_zone, drone)
                if conn:
                    conn.current_usage += 1
                drone.start_flight(conn, target_zone)
                conn_name = (
                    f"{conn.zone_a.name}-{conn.zone_b.name}"
                    if conn
                    else target_zone.name
                )
                movements.append(f"{drone.label}-{conn_name}")

            elif action_type == "move":
                self._free_zone(drone.current_zone, drone)
                if conn:
                    conn.current_usage += 1
                drone.move_to(target_zone)
                if conn:
                    conn.current_usage -= 1
                self._occupy_zone(target_zone, drone)
                movements.append(f"{drone.label}-{target_zone.name}")

                if target_zone == self.graph.end:
                    drone.mark_delivered()

        return " ".join(movements)

    def _decide(
            self, drone: Drone
    ) -> Optional[tuple[str, Zone, Optional[Connection]]]:
        """Decide the next action for a drone.

        Args:
            drone: The drone to decide for.

        Returns:
            A tuple of (action_type, target_zone, connection) or None if no action.
        """

        if drone.is_in_flight():
            dest = drone.flight_destination
            conn = drone.flight_connection
            if dest is not None:
                return ("flight_complete", dest, conn)
            return None

        next_zone = drone.next_zone()
        if next_zone is None:
            return None

        conn = self._find_connection(drone.current_zone, next_zone)
        if conn is None:
            return None

        if next_zone.zone_type == ZoneType.RESTRICTED:
            return ("flight_start", next_zone, conn)

        return ("move", next_zone, conn)

    def _find_connection(
            self, zone_a: Zone, zone_b: Zone
    ) -> Optional[Connection]:
        """Find the connection between two zones.

        Args:
            zone_a: The first zone.
            zone_b: The second zone.

        Returns:
            The connection if found, None otherwise.
        """
        for conn in self.graph.adjacency[zone_a.name]:
            if conn.other_zone(zone_a) == zone_b:
                return conn
        return None

    def _resolve_conflicts(
            self,
            intentions: dict[int, Optional[tuple[str, Zone, Optional[Connection]]]]
    ) -> dict[int, Optional[tuple[str, Zone, Optional[Connection]]]]:
        """Validate intentions against capacity constraints.

            Drones in flight (turn 2) always have priority — they MUST arrive.
            Other drones are validated in order, first come first served.

            Args:
                intentions: Raw intended actions per drone id.

            Returns:
                Validated actions — drones that can't move get None (wait).
        """
        validated: dict[
            int, Optional[tuple[str, Zone, Optional[Connection]]]
        ] = {}

        zone_incoming: dict[str, int] = {}
        zone_outgoing: dict[str, int] = {}
        link_usage: dict[str, int] = {}
        for drone in self.drones:
            if drone.delivered:
                validated[drone.drone_id] = None
                continue
            action = intentions[drone.drone_id]
            if action and action[0] == "flight_complete":
                dest = action[1]
                validated[drone.drone_id] = action
                zone_incoming[dest.name] = zone_incoming.get(dest.name, 0) + 1
                zone_outgoing[drone.current_zone.name] = zone_outgoing.get(drone.current_zone.name, 0) + 1

        for drone in self.drones:
            if drone.delivered or drone.drone_id in validated:
                continue

            action = intentions[drone.drone_id]
            if action is None:
                validated[drone.drone_id] = None
                continue

            act_type, dest, conn = action

            current_in_dest = dest.current_drones
            outgoing_from_dest = zone_outgoing.get(dest.name, 0)
            incoming_to_dest = zone_incoming.get(dest.name, 0)
            effective_count = (
                current_in_dest + incoming_to_dest - outgoing_from_dest
            )

            zone_ok = dest.is_end or dest.is_start or (
                effective_count < dest.max_drones
            )

            link_key = (
                f"{min(dest.name, drone.current_zone.name)}"
                f"-{max(dest.name, drone.current_zone.name)}"
            )
            link_used = link_usage.get(link_key, 0)
            link_ok = conn is None or (
                link_used + conn.current_usage < conn.max_link_capacity
            )

            if zone_ok and link_ok:
                validated[drone.drone_id] = action
                zone_incoming[dest.name] = incoming_to_dest + 1
                zone_outgoing[drone.current_zone.name] = (
                    zone_outgoing.get(drone.current_zone.name, 0) + 1
                )
                if conn:
                    link_usage[link_key] = link_used + 1
            else:
                validated[drone.drone_id] = None

        return validated

    def _occupy_zone(self, zone: Zone, drone: Drone) -> None:
        """Increment occupancy counter for a zone.

        Args:
            zone:  Zone being entered.
            drone: Drone entering it (unused but useful for future logging).
        """
        if not zone.is_start and not zone.is_end:
            zone.current_drones += 1

    def _free_zone(self, zone: Zone, drone: Drone) -> None:
        """Decrement occupancy counter for a zone.

        Args:
            zone:  Zone being exited.
            drone: Drone exiting it (unused but useful for future logging).
        """
        if not zone.is_start and not zone.is_end:
            zone.current_drones = max(0, zone.current_drones - 1)

    # def print_log(self) -> None:
    #     """Print the simulation log."""
    #     for line in self.log:
    #         print(line)
    #     print(f"\nTotal turns: {self.turn}")
