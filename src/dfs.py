import random

from .maze_generator import Grid, Point


class MazeGenerator:
    def __init__(self, grid: Grid, seed: int | None = None):
        self.grid = grid
        self.rng = random.Random(seed)
        self.visited = set()
        self.stack = []

    def get_unvisited_neighbors(self, point: Point) -> list[Point]:
        return [
            neighbor
            for neighbor in self.grid.get_playable_neighbors(point)
            if neighbor not in self.visited
        ]

    def generate(self):
        self.visited.add(self.grid.start)
        self.stack.append(self.grid.start)
        while self.stack:
            current = self.stack[-1]
            neigbours = self.get_unvisited_neighbors(current)
            if not neigbours:
                self.stack.pop()
            else:
                rand = self.rng.choice(neigbours)
                self.visited.add(rand)
                self.stack.append(rand)
                self.grid.open_passage(current, rand)

        if len(self.visited) != self.grid.playable_cell_count:
            raise ValueError("Playable maze cells are disconnected")

        if not self.grid.perfect:
            self.remove_dead_ends()
            self.check_corners_center()
            self.add_extra_passages()

    def count_open_neighbors(self, point: Point) -> int:
        return len(self.grid.get_open_playable_neighbors(point))

    def remove_dead_ends(self) -> None:
        for point in self.grid.iter_playable_cells():
            if self.count_open_neighbors(point) == 1:
                possibilities = self.grid.get_closed_playable_neighbors(point)
                if possibilities:
                    self.grid.open_passage(point, self.rng.choice(possibilities))

    def add_extra_passages(self) -> None:
        is_option = True
        while self.count_loops() < 2 and is_option:
            is_option = False
            for point in self.grid.iter_playable_cells():
                possibilities = self.grid.get_closed_playable_neighbors(point)
                if possibilities:
                    self.grid.open_passage(point, self.rng.choice(possibilities))
                    if self.count_loops() >= 2:
                        return
                    is_option = True
                    break

    def count_loops(self):
        vertices = self.grid.playable_cell_count
        edges = sum(
            self.count_open_neighbors(point)
            for point in self.grid.iter_playable_cells()
        ) // 2
        return edges - vertices + 1

    # TODO ну тут вот центр как-то ебануть и красиво будет
    # def get_center_cells(self):
    def check_corners_center(self):
        corners = (
            Point(0, 0),
            Point(self.grid.width - 1, 0),
            Point(0, self.grid.height - 1),
            Point(self.grid.width - 1, self.grid.height - 1)
        )
        center = Point(self.grid.width // 2, self.grid.height // 2)  # todo
        for c in [center, *corners]:
            if not self.grid.is_playable(c):
                continue
            while self.count_open_neighbors(c) < 2:
                open_neibs = self.grid.get_closed_playable_neighbors(c)
                if open_neibs:
                    r = self.rng.choice(open_neibs)
                    self.grid.open_passage(c, r)
                else:
                    break
