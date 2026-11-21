"""Shared non-perfect maze post-processing helpers."""

import random
from collections.abc import Callable

from .maze_generator import Grid, Point


def clone_grid(grid: Grid) -> Grid:
    """Copy a grid, including wall flags and reserved cells."""
    cloned = Grid(
        grid.width,
        grid.height,
        grid.start,
        grid.end,
        grid.perfect,
    )
    cloned.reserve_cells(grid.reserved_cells)
    for y in range(grid.height):
        for x in range(grid.width):
            cloned.cells[y][x] = grid.cells[y][x]
    return cloned


def has_three_by_three_open_area(grid: Grid) -> bool:
    """Return True if any fully open 3x3 area exists."""
    if grid.width < 3 or grid.height < 3:
        return False
    for y in range(grid.height - 2):
        for x in range(grid.width - 2):
            points = [
                Point(px, py)
                for py in range(y, y + 3)
                for px in range(x, x + 3)
            ]
            if not all(grid.is_playable(point) for point in points):
                continue
            fully_open = True
            for py in range(y, y + 3):
                for px in range(x, x + 2):
                    left = Point(px, py)
                    right = Point(px + 1, py)
                    if not grid.is_open_passage(left, right):
                        fully_open = False
                        break
                if not fully_open:
                    break
            if fully_open:
                for py in range(y, y + 2):
                    for px in range(x, x + 3):
                        top = Point(px, py)
                        bottom = Point(px, py + 1)
                        if not grid.is_open_passage(top, bottom):
                            fully_open = False
                            break
                    if not fully_open:
                        break
            if fully_open:
                return True
    return False


def can_open_without_large_area(
    grid: Grid,
    point1: Point,
    point2: Point,
) -> bool:
    """Check whether opening an edge keeps corridors at most 2 cells wide."""
    simulated = clone_grid(grid)
    if not simulated.open_passage(point1, point2):
        return False
    return not has_three_by_three_open_area(simulated)


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
