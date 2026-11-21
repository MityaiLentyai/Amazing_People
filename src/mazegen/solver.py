from collections import deque

from .maze_generator import Grid, Point


class BFS:
    def __init__(self, grid: Grid):
        self.grid = grid

    def get_accessible_neighbors(self, point: Point) -> list[Point]:
        return self.grid.get_open_playable_neighbors(point)

    def reconstruct_path(self, parent: dict[Point, Point | None]) -> list[Point]:
        path = [self.grid.end]
        current = self.grid.end
        while parent[current] is not None:
            path.append(parent[current])
            current = parent[current]
        path.reverse()
        return path

    def find_path(self) -> list[Point] | None:
        if not self.grid.is_playable(self.grid.start) or not self.grid.is_playable(
            self.grid.end
        ):
            return None

        visited = {self.grid.start}
        queue = deque([self.grid.start])
        parent: dict[Point, Point | None] = {self.grid.start: None}
        while queue:
            current = queue.popleft()
            if current == self.grid.end:
                return self.reconstruct_path(parent)
            for neighbor in self.get_accessible_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    parent[neighbor] = current

        return None

    def get_direction(self, path: list[Point]) -> list[str]:
        result = []
        for current, following in zip(path, path[1:]):
            if current.x > following.x:
                result.append("W")
            elif current.x < following.x:
                result.append("E")
            elif current.y > following.y:
                result.append("N")
            elif current.y < following.y:
                result.append("S")

        return result