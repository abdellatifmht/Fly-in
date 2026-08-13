class SimulationOutput:
    """Formats and prints simulation results.

    Attributes:
        total_turns: Total turns the simulation ran.
        nb_drones:   Total number of drones.
    """

    def __init__(self, total_turns: int, nb_drones: int) -> None:
        self.total_turns = total_turns
        self.nb_drones = nb_drones

    def print_summary(self, log: list[str]) -> None:
        """Print the full turn-by-turn log and final metrics.

        Args:
            log: List of turn output strings.
        """
        for line in log:
            if line:
                print(line)

        print("\n--- Simulation complete ---")
        print(f"Total turns : {self.total_turns}")
        print(f"Drones      : {self.nb_drones}")
        avg = self.total_turns / self.nb_drones if self.nb_drones else 0
        print(f"Avg turns/drone: {avg:.1f}")
