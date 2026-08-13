import heapq
from typing import Optional
from models import Zone, ZoneType, Graph


class Dijkstra:
    """Weighted shortest path using zone movement costs.

    Attributes:
        graph: The zone graph to search in.
    """
    def __init__(self, graph: Graph):
        self.graph = graph

    def find_path(
            self,
            start: Zone,
            end: Zone,
    ) -> Optional[list[Zone]]:
        """Finds the shortest path from start to end using Dijkstra's algorithm.

        Args:
            start: The starting zone.
            end: The destination zone.

        Returns:
            A list of zones representing the shortest path from start to end, or None if no path exists.
        """
        heap: list[tuple[int, int, str]] = []
        heapq.heappush(heap, (0, 1, start.name))

        costs: dict[str, int] = {start.name: 0}
        previous: dict[str, Optional[str]] = {start.name: None}

        while heap:
            cost, _, current_name = heapq.heappop(heap)

            if current_name == end.name:
                return self._reconstruct_path(previous, end.name)

            if cost > costs.get(current_name, float('inf')):
                continue

            current_zone = self.graph.zones[current_name]

            for neighbor, connection in self.graph.get_neighbors(current_zone):
                if neighbor.zone_type == ZoneType.BLOCKED:
                    continue

                move_cost = neighbor.movement_cost()
                new_cost = cost + move_cost

                if new_cost < costs.get(neighbor.name, float('inf')):
                    costs[neighbor.name] = new_cost
                    previous[neighbor.name] = current_name

                    bonus = 0 if neighbor.zone_type == ZoneType.PRIORITY else 1
                    heapq.heappush(heap, (new_cost, bonus, neighbor.name))

        return None

    def find_all_paths(
            self,
            start: Zone,
            end: Zone,
            max_paths: int = 5
    ) -> list[list[Zone]]:
        """Finds multiple paths for multi-drone distribution.
        Uses repeated Djikstra with zone exclusions to find disjoint paths.

        Args:
            start: The starting zone.
            end: The destination zone.
            max_paths: The maximum number of paths to find.

        Returns:
            A list of lists, where each inner list represents a path from start to end.
        """
        paths: list[list[Zone]] = []
        excluded: set[str] = set()

        for _ in range(max_paths):
            path = self._find_path_excluding(start, end, excluded)
            if path is None:
                break
            paths.append(path)

            for zone in path[1:-1]:
                excluded.add(zone.name)

        return paths

    def _find_path_excluding(
            self,
            start: Zone,
            end: Zone,
            excluded: set[str]
    ) -> Optional[list[Zone]]:
        """Dijkstra while skipping a set of excluded intermediate zones.

        Args:
            start:    Starting zone.
            end:      Destination zone.
            excluded: Zone names to skip (intermediate zones only).

        Returns:
            Path as list of zones, or None.
        """
        heap: list[tuple[int, int, str]] = []
        heapq.heappush(heap, (0, 1, start.name))

        costs: dict[str, int] = {start.name: 0}
        previous: dict[str, Optional[str]] = {start.name: None}

        while heap:
            cost, _, current_name = heapq.heappop(heap)

            if current_name == end.name:
                return self._reconstruct_path(previous, end.name)

            if cost > costs.get(current_name, float("inf")):
                continue

            current_zone = self.graph.zones[current_name]

            for neighbor, connection in self.graph.get_neighbors(current_zone):
                if neighbor.zone_type == ZoneType.BLOCKED or neighbor.name in excluded:
                    continue

                move_cost = neighbor.movement_cost()
                new_cost = cost + move_cost

                if new_cost < costs.get(neighbor.name, float("inf")):
                    costs[neighbor.name] = new_cost
                    previous[neighbor.name] = current_name

                    bonus = 0 if neighbor.zone_type == ZoneType.PRIORITY else 1
                    heapq.heappush(heap, (new_cost, bonus, neighbor.name))

        return None

    def _reconstruct_path(
            self,
            previous: dict[str, Optional[str]],
            end_name: str
    ) -> list[Zone]:
        """Reconstructs the path from the previous dictionary.

        Args:
            previous: A dictionary mapping zone names to their predecessors.
            end_name: The name of the destination zone.

        Returns:
            A list of zones representing the path from start to end.
        """
        path: list[Zone] = []
        current_name: Optional[str] = end_name

        while current_name is not None:
            path.append(self.graph.zones[current_name])
            current_name = previous.get(current_name)

        path.reverse()
        return path
