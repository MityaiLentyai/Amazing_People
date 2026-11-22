"""Shared non-perfect maze post-processing helpers."""

import random
from collections.abc import Callable

from .maze_generator import Grid, Point


def _is_open_3x3_after_removal(
    grid: Grid,
    x: int,
    y: int,
    removed_wall: tuple[Point, Point],
) -> bool:
    """Check all internal passages, treating the candidate wall as open."""
    for row in range(y, y + 3):
        for column in range(x, x + 3):
            cell = Point(column, row)
            if column < x + 2:
                right = Point(column + 1, row)
                if (cell, right) != removed_wall and not grid.is_open_passage(
                    cell, right
                ):
                    return False
            if row < y + 2:
                below = Point(column, row + 1)
                if (cell, below) != removed_wall and not grid.is_open_passage(
                    cell, below
                ):
                    return False
    return True


def can_open_without_large_area(
    grid: Grid,
    point1: Point,
    point2: Point,
) -> bool:
    """Check whether opening a passage creates a fully open 3x3 area.

    Post-processing starts with a spanning tree and preserves the absence
    of open 3x3 areas, so only windows spanning this wall can become open.
    """
    if point2 not in grid.get_playable_neighbors(point1):
        return False

    if point1.x > point2.x or point1.y > point2.y:
        point1, point2 = point2, point1
    removed_wall = (point1, point2)
    first_x = max(0, point2.x - 2)
    last_x = min(grid.width - 3, point1.x)
    first_y = max(0, point2.y - 2)
    last_y = min(grid.height - 3, point1.y)

    for y in range(first_y, last_y + 1):
        for x in range(first_x, last_x + 1):
            if _is_open_3x3_after_removal(grid, x, y, removed_wall):
                return False
    return True


class PostProcessor:
    """Apply shared Pac-Man-oriented post-processing to a spanning tree."""

    def __init__(
        self,
        grid: Grid,
        rng: random.Random,
        open_passage: Callable[[Point, Point], bool],
    ) -> None:
        self.grid = grid
        self.rng = rng
        self.open_passage = open_passage

    def count_open_neighbors(self, point: Point) -> int:
        """Count open playable passages from a point."""
        return len(self.grid.get_open_playable_neighbors(point))

    def count_loops(self) -> int:
        """Count independent cycles in the playable graph."""
        vertices = self.grid.playable_cell_count
        edges = sum(
            self.count_open_neighbors(point)
            for point in self.grid.iter_playable_cells()
        ) // 2
        return edges - vertices + 1

    def remove_dead_ends(self) -> None:
        """Open an alternative wall from each simple dead-end."""
        for point in self.grid.iter_playable_cells():
            if self.count_open_neighbors(point) != 1:
                continue
            possibilities = self.grid.get_closed_playable_neighbors(point)
            if possibilities:
                self.rng.shuffle(possibilities)
                for neighbor in possibilities:
                    if self.open_passage(point, neighbor):
                        break

    def ensure_key_corridors(self) -> None:
        """Keep the four corners and centre as open corridors."""
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
                possibilities = (
                    self.grid.get_closed_playable_neighbors(point)
                )
                if not possibilities:
                    break
                self.rng.shuffle(possibilities)
                opened = False
                for neighbor in possibilities:
                    if self.open_passage(point, neighbor):
                        opened = True
                        break
                if not opened:
                    break

    def add_extra_passages(self) -> None:
        """Open enough passages to provide at least two independent loops."""
        while self.count_loops() < 2:
            opened = False
            for point in self.grid.iter_playable_cells():
                possibilities = (
                    self.grid.get_closed_playable_neighbors(point)
                )
                if not possibilities:
                    continue
                self.rng.shuffle(possibilities)
                for neighbor in possibilities:
                    if self.open_passage(point, neighbor):
                        opened = True
                        break
                if opened:
                    break
            if not opened:
                return

    def process(self) -> None:
        """Run the complete non-perfect post-processing pipeline."""
        self.remove_dead_ends()
        self.ensure_key_corridors()
        self.add_extra_passages()
