*This project has been created as part of the 42 curriculum by <login>.*

## Description

**Fly-in** is a drone routing simulation system written in Python.
The goal is to move a fleet of drones from a start zone to an end zone
through a network of connected zones, in the fewest possible simulation turns.

The system handles:
- Weighted pathfinding (normal / restricted / priority / blocked zones)
- Multi-drone simultaneous movement
- Zone and connection capacity constraints
- 2-turn transit for restricted zones
- Conflict resolution and deadlock avoidance

## Instructions

### Install dependencies
```bash
make install
```

### Run simulation
```bash
make run MAP=maps/easy_1.map
```

### Debug mode
```bash
make debug MAP=maps/easy_1.map
```

### Lint
```bash
make lint
```

### Clean
```bash
make clean
```

## Algorithm

### Pathfinding — Dijkstra
Each drone is assigned a path using a weighted Dijkstra algorithm:
- `normal` zone → cost 1
- `priority` zone → cost 1 (preferred over normal on equal cost)
- `restricted` zone → cost 2 (2-turn transit)
- `blocked` zone → inaccessible

### Multi-drone scheduling
Paths are distributed across drones using `find_all_paths`, which runs
Dijkstra repeatedly while excluding intermediate zones already used,
producing disjoint or partially disjoint paths to maximize throughput.

### Conflict resolution
Each turn, the engine resolves conflicts in two passes:
1. Drones completing restricted transit (turn 2) always have priority
2. Other drones validated first-come first-served against zone/link capacity

## Visual Representation

The terminal visualizer displays:
- Per-turn header with turn number
- Each drone movement colored (drone label in magenta, destination in cyan)
- Zone state table showing occupancy, zone type, and drone positions
- Final summary with total turns, drone count, and average turns per drone

Colors follow zone metadata from the map file, with fallback to zone type defaults.

## Resources

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [BFS — Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
- [Python heapq docs](https://docs.python.org/3/library/heapq.html)
- [PEP 257 — Docstrings](https://peps.python.org/pep-0257/)
- [mypy documentation](https://mypy.readthedocs.io/)

### AI usage
Claude was used to help scaffold the initial class structure and identify
bugs in the conflict resolution logic. All code was reviewed, understood,
and adapted manually. The algorithm design and simulation logic were
developed and validated independently.