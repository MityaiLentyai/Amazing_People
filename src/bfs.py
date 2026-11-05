from collections import deque

from .maze_generator import Grid, Point


class BFS:
    def __init__(self, grid: Grid):
        self.grid = grid

    def get_accessible_neighbors(self, point: Point) -> list[Point]:
        return self.grid.get_open_playable_neighbors(point)

    def reconstruct_path(self, parent: dict[Point, Point | None]) -> list[
        Point]:
        path = [self.grid.end]
        current = self.grid.end
        while parent[current] is not None:
            path.append(parent[current])
            current = parent[current]
        path.reverse()
        return path

    def find_path(self):
        if not self.grid.is_playable(self.grid.start) or not self.grid.is_playable(
            self.grid.end
        ):
            return None

        visited = set()
        queue = deque()
        queue.append(self.grid.start)
        visited.add(self.grid.start)
        parent = {self.grid.start: None}
        while queue:
            current = queue.popleft()
            if current == self.grid.end:
                return self.reconstruct_path(parent)
            neigbours = self.get_accessible_neighbors(current)
            for n in neigbours:
                if n not in visited:
                    visited.add(n)
                    queue.append(n)
                    parent[n] = current

        return None

    def get_direction(self, path: list[Point]):
        result = []
        for i in range(len(path) - 1):
            if path[i].x > path[i + 1].x:
                result.append('W')
            elif path[i].x < path[i + 1].x:
                result.append('E')
            elif path[i].y > path[i + 1].y:
                result.append('N')
            elif path[i].y < path[i + 1].y:
                result.append('S')

        return result
