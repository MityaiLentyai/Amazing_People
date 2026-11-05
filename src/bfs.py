from collections import deque

from .maze_generator import Grid, Point, Wall


class BFS:
    def __init__(self, grid: Grid):
        self.grid = grid

    def get_accessible_neighbors(self, point: Point) -> list[Point]:
        neighbours = []
        if not self.grid.cells[point.y][point.x] & Wall.NORTH and point.y > 0:
            neighbours.append(Point(x=point.x, y=point.y - 1))
        if not self.grid.cells[point.y][
                   point.x] & Wall.EAST and point.x < self.grid.width - 1:
            neighbours.append(Point(x=point.x + 1, y=point.y))
        if not self.grid.cells[point.y][point.x] & Wall.WEST and point.x > 0:
            neighbours.append(Point(x=point.x - 1, y=point.y))
        if not self.grid.cells[point.y][
                   point.x] & Wall.SOUTH and point.y < self.grid.height - 1:
            neighbours.append(Point(x=point.x, y=point.y + 1))
        return neighbours

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
