import sys
from map_parser import MapParser, ParserError
from engine import SimulationEngine


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
    engine.run()


if __name__ == "__main__":
    main()
