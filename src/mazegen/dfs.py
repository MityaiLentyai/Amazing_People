import random

from .maze_generator import Grid, Point
from .post_processing import PostProcessor, can_open_without_large_area


class DFSGenerator:
    def __init__(
        self,
        grid: Grid,
        seed: int | None = None,
        generation_steps: list[tuple[Point, Point]] | None = None,
    ):
        self.grid = grid
        self.rng = random.Random(seed)
        self.visited: set[Point] = set()
        self.stack: list[Point] = []
        self.generation_steps = generation_steps

    def open_passage(self, point1: Point, point2: Point) -> None:
        was_open = self.grid.is_open_passage(point1, point2)
        if self.grid.open_passage(point1, point2) and not was_open:
            if self.generation_steps is not None:
                self.generation_steps.append((point1, point2))

    def try_postprocessing_passage(
        self,
        point1: Point,
        point2: Point,
    ) -> bool:
        """Safely open a passage during non-perfect post-processing."""
        if self.grid.is_open_passage(point1, point2):
            return False
        if not can_open_without_large_area(self.grid, point1, point2):
            return False
        was_open = self.grid.is_open_passage(point1, point2)
        if self.grid.open_passage(point1, point2) and not was_open:
            if self.generation_steps is not None:
                self.generation_steps.append((point1, point2))
            return True
        return False

    def get_unvisited_neighbors(self, point: Point) -> list[Point]:
        return [
            neighbor
            for neighbor in self.grid.get_playable_neighbors(point)
            if neighbor not in self.visited
        ]

    def generate(self) -> None:
        """Generate and optionally post-process the maze."""
        self.visited.add(self.grid.start)
        self.stack.append(self.grid.start)
        while self.stack:
            current = self.stack[-1]
            neighbours = self.get_unvisited_neighbors(current)
            if not neighbours:
                self.stack.pop()
            else:
                rand = self.rng.choice(neighbours)
                self.visited.add(rand)
                self.stack.append(rand)
                self.open_passage(current, rand)

        if len(self.visited) != self.grid.playable_cell_count:
            raise ValueError("Playable maze cells are disconnected")

        if not self.grid.perfect:
            PostProcessor(
                self.grid,
                self.rng,
                self.try_postprocessing_passage,
            ).process()


MazeGenerator = DFSGenerator
