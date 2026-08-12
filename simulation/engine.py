from typing import Optional
from models.drone import Drone, DroneState
from models.zone import Zone
from models.connection import Connection
from models.graph import Graph
from pathfinding import dijkstra


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
        self.dijkstra = dijkstra
        self.turn: int = 0
        self.log: list[str] = []

        def setup(self) -> None:
            """Creates drones and assign initial paths."""
            if self.graph.start_zone is None or self.graph.end_zone is None:
                raise RuntimeError("Start and end zones must be defined in the graph.")

            paths = self.dijkstra(
                self.graph.start_zone,
                self.graph.end_zone,
                max_paths=self.graph.nb_drones
                )

            if not paths:
                raise RuntimeError("No paths found from start to end zone.")

            for i in range(1, self.graph.nb_drones + 1):
                drone = Drone(i, self.graph.start)
                path = [(i - 1) % len(paths)]
                drone.assign_path(path)
                self.drones.append(drone)

            self.graph.start.current_drones = self.graph.nb_drones

    def run(self) -> int:
        """Run the full simulation until all drones are delivered.

        Returns:
            The total number of turns used.
        """
        self.setup()
        while not self._alldelivered():
            self.turn += 1
            turn_output = self._run_turn()
            if turn_output:
                self.log.append(turn_output)

        return self.turn

    def _alldelivered(self) -> bool:
        """Check if all drones have completed their deliveries.

        Returns:
            True if all drones are delivered, False otherwise.
        """
        return all(drone.delivered for drone in self.drones)

    # def _run_turn(self) -> str:
    #     """Execute one simulation turn.

    #     Returns:
    #         A string representing the output for the current turn.
    #     """
