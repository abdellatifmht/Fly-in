import sys
from parser.map_parser import MapParser, ParserError
from simulation.engine import SimulationEngine
from simulation.output import SimulationOutput


def main() -> None:
    """Entry point — parse map file and run simulation."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <map_file>")
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        graph = MapParser().parse(filepath)
    except ParserError as e:
        print(f"Parse error: {e}")
        sys.exit(1)

    engine = SimulationEngine(graph)
    total_turns = engine.run()

    # output = SimulationOutput(total_turns, graph.nb_drones)
    # output.print_summary(engine.log)


if __name__ == "__main__":
    main()
