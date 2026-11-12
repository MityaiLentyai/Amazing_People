import random

from .maze_generator import Grid, Point


class MazeGenerator:
    def __init__(
        self,
        grid: Grid,
        seed: int | None = None,
        generation_steps: list[tuple[Point, Point]] | None = None,
    ) -> None:
        self.grid = grid
        self.rng = random.Random(seed)
        self.visited: set[Point] = set()
        self.generation_steps = generation_steps

    def open_passage(self, point1: Point, point2: Point) -> None:
        was_open = self.grid.is_open_passage(point1, point2)
        if self.grid.open_passage(point1, point2) and not was_open:
            if self.generation_steps is not None:
                self.generation_steps.append((point1, point2))

    def get_unvisited_neighbors(self, point: Point) -> list[Point]:
        return [
            neighbor
            for neighbor in self.grid.get_playable_neighbors(point)
            if neighbor not in self.visited
        ]

    def generate(self) -> None:
        if not self.grid.is_playable(self.grid.start):
            raise ValueError("Entry cell must be playable")

        self.visited.add(self.grid.start)
        frontier = [
            (self.grid.start, neighbor)
            for neighbor in self.get_unvisited_neighbors(self.grid.start)
        ]

        while frontier:
            index = self.rng.randrange(len(frontier))
            current, neighbor = frontier[index]
            frontier[index] = frontier[-1]
            frontier.pop()

            if neighbor in self.visited:
                continue

            self.open_passage(current, neighbor)
            self.visited.add(neighbor)
            frontier.extend(
                (neighbor, candidate)
                for candidate in self.get_unvisited_neighbors(neighbor)
            )

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
                    self.open_passage(point, self.rng.choice(possibilities))

    def check_corners_center(self) -> None:
        points = (
            Point(self.grid.width // 2, self.grid.height // 2),
            Point(0, 0),
            Point(self.grid.width - 1, 0),
            Point(0, self.grid.height - 1),
            Point(self.grid.width - 1, self.grid.height - 1),
        )
        for point in points:
            if not self.grid.is_playable(point):
                continue
            while self.count_open_neighbors(point) < 2:
                possibilities = self.grid.get_closed_playable_neighbors(point)
                if not possibilities:
                    break
                self.open_passage(point, self.rng.choice(possibilities))

    def count_loops(self) -> int:
        edges = sum(
            self.count_open_neighbors(point)
            for point in self.grid.iter_playable_cells()
        ) // 2
        return edges - self.grid.playable_cell_count + 1

    def add_extra_passages(self) -> None:
        loops_needed = 2 - self.count_loops()
        for point in self.grid.iter_playable_cells():
            while loops_needed > 0:
                possibilities = self.grid.get_closed_playable_neighbors(point)
                if not possibilities:
                    break
                self.open_passage(point, self.rng.choice(possibilities))
                loops_needed -= 1
            if loops_needed <= 0:
                return
