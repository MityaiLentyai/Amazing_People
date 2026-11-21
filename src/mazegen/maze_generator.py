import random
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import IntFlag


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class Wall(IntFlag):
    NONE = 0
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8
    ALL = NORTH | EAST | SOUTH | WEST


WALLS_BY_DIRECTION = {
    (0, -1): (Wall.NORTH, Wall.SOUTH),
    (1, 0): (Wall.EAST, Wall.WEST),
    (0, 1): (Wall.SOUTH, Wall.NORTH),
    (-1, 0): (Wall.WEST, Wall.EAST),
}
ALGORITHMS = ("dfs", "prim")


class Grid:
    def __init__(
        self,
        width: int,
        height: int,
        start: Point,
        end: Point,
        perfect: bool,
    ):
        self.width = width
        self.height = height
        self.start = start
        self.end = end
        self.perfect = perfect
        self.cells = [[Wall.ALL for _ in range(width)] for _ in range(height)]
        self.reserved_cells: set[Point] = set()

    def is_inside(self, point: Point) -> bool:
        return 0 <= point.x < self.width and 0 <= point.y < self.height

    def is_playable(self, point: Point) -> bool:
        return self.is_inside(point) and point not in self.reserved_cells

    @property
    def playable_cell_count(self) -> int:
        return self.width * self.height - len(self.reserved_cells)

    def iter_playable_cells(self) -> Iterator[Point]:
        for y in range(self.height):
            for x in range(self.width):
                point = Point(x, y)
                if self.is_playable(point):
                    yield point

    def get_playable_neighbors(self, point: Point) -> list[Point]:
        if not self.is_playable(point):
            return []

        neighbors = (
            Point(point.x - 1, point.y),
            Point(point.x + 1, point.y),
            Point(point.x, point.y - 1),
            Point(point.x, point.y + 1),
        )
        return [neighbor for neighbor in neighbors if self.is_playable(neighbor)]

    def _wall_pair(
        self,
        point1: Point,
        point2: Point,
    ) -> tuple[Wall, Wall] | None:
        direction = (point2.x - point1.x, point2.y - point1.y)
        return WALLS_BY_DIRECTION.get(direction)

    def is_open_passage(self, point1: Point, point2: Point) -> bool:
        if not self.is_playable(point1) or not self.is_playable(point2):
            return False

        walls = self._wall_pair(point1, point2)
        if walls is None:
            return False

        wall1, wall2 = walls
        return not (self.cells[point1.y][point1.x] & wall1) and not (
            self.cells[point2.y][point2.x] & wall2
        )

    def get_open_playable_neighbors(self, point: Point) -> list[Point]:
        return [
            neighbor
            for neighbor in self.get_playable_neighbors(point)
            if self.is_open_passage(point, neighbor)
        ]

    def get_closed_playable_neighbors(self, point: Point) -> list[Point]:
        closed = []
        for neighbor in self.get_playable_neighbors(point):
            walls = self._wall_pair(point, neighbor)
            if walls is None:
                continue
            wall1, wall2 = walls
            if (self.cells[point.y][point.x] & wall1) and (
                self.cells[neighbor.y][neighbor.x] & wall2
            ):
                closed.append(neighbor)
        return closed

    def reserve_cells(self, points: Iterable[Point]) -> None:
        cells = set(points)
        if any(not self.is_inside(point) for point in cells):
            raise ValueError("Reserved cells must be inside the grid")
        if self.start in cells or self.end in cells:
            raise ValueError("Entry and exit cells cannot be reserved")

        self.reserved_cells.update(cells)
        for point in cells:
            self.cells[point.y][point.x] = Wall.ALL
            for (dx, dy), (_, neighbor_wall) in WALLS_BY_DIRECTION.items():
                neighbor = Point(point.x + dx, point.y + dy)
                if self.is_inside(neighbor):
                    self.cells[neighbor.y][neighbor.x] |= neighbor_wall

    def open_passage(self, point1: Point, point2: Point) -> bool:
        """Open a shared wall between adjacent playable cells."""
        if not self.is_playable(point1) or not self.is_playable(point2):
            return False

        walls = self._wall_pair(point1, point2)
        if walls is None:
            return False

        wall1, wall2 = walls
        self.cells[point1.y][point1.x] &= ~wall1
        self.cells[point2.y][point2.x] &= ~wall2
        return True


class MazeGenerator:
    """Generate and solve a maze without application-specific dependencies."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: Point | tuple[int, int],
        exit: Point | tuple[int, int],
        perfect: bool = True,
        seed: int | None = None,
        algorithm: str = "dfs",
    ) -> None:
        if not isinstance(width, int) or isinstance(width, bool) or width < 1:
            raise ValueError("Width must be a positive integer")
        if not isinstance(height, int) or isinstance(height, bool) or height < 1:
            raise ValueError("Height must be a positive integer")

        self.width = width
        self.height = height
        self.entry = self._point(entry, "entry")
        self.exit = self._point(exit, "exit")
        if not self._inside(self.entry):
            raise ValueError("Entry cell must be inside the grid")
        if not self._inside(self.exit):
            raise ValueError("Exit cell must be inside the grid")
        if self.entry == self.exit:
            raise ValueError("Entry and exit cells must be different")

        normalized_algorithm = algorithm.lower() if isinstance(algorithm, str) else ""
        if normalized_algorithm not in ALGORITHMS:
            raise ValueError(f"Algorithm must be one of: {', '.join(ALGORITHMS)}")

        self.perfect = perfect
        self.seed = seed
        self.algorithm = normalized_algorithm
        self._used_seeds = {seed} if seed is not None else set()
        self.generation_steps: list[tuple[Point, Point]] = []
        self.grid = self._new_grid()
        self.path: list[Point] | None = None
        self.directions: list[str] = []

    @staticmethod
    def _point(value: Point | tuple[int, int], name: str) -> Point:
        if isinstance(value, Point):
            x, y = value.x, value.y
        else:
            try:
                x, y = value
            except (TypeError, ValueError):
                raise ValueError(
                    f"{name.title()} must be a Point or an (x, y) pair"
                ) from None
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError(f"{name.title()} coordinates must be integers")
        return Point(x, y)

    def _inside(self, point: Point) -> bool:
        return 0 <= point.x < self.width and 0 <= point.y < self.height

    def _new_grid(self) -> Grid:
        return Grid(self.width, self.height, self.entry, self.exit, self.perfect)

    def generate(self) -> Grid:
        """Create a fresh maze and cache its shortest path and directions."""
        from .pattern_42 import get_42_cells

        self.generation_steps.clear()
        self.grid = self._new_grid()
        self.path = None
        self.directions = []
        glyph_cells = get_42_cells(
            self.width, self.height, self.entry, self.exit, self.perfect
        )
        if glyph_cells is not None:
            self.grid.reserve_cells(glyph_cells)

        if self.algorithm == "dfs":
            from .dfs import DFSGenerator

            generator_type = DFSGenerator
        else:
            from .primm import PrimGenerator

            generator_type = PrimGenerator

        generator_type(
            self.grid,
            seed=self.seed,
            generation_steps=self.generation_steps,
        ).generate()
        self.solve()
        return self.grid

    def regenerate(self, seed: int | None = None) -> Grid:
        """Generate another maze, using a seed not used by this instance."""
        seed_source = random.SystemRandom()
        if seed is None:
            seed = seed_source.randrange(0, 2**32)
            while seed in self._used_seeds:
                seed = seed_source.randrange(0, 2**32)
        elif seed in self._used_seeds:
            raise ValueError("Seed has already been used by this generator")

        self._used_seeds.add(seed)
        self.seed = seed
        return self.generate()

    def solve(self) -> list[Point] | None:
        """Find and cache a shortest path from the entry to the exit."""
        from .solver import BFS

        solver = BFS(self.grid)
        self.path = solver.find_path()
        self.directions = solver.get_direction(self.path) if self.path else []
        return self.path

    def to_hex_rows(self) -> list[str]:
        """Return the grid as uppercase hexadecimal wall-flag rows."""
        return [
            "".join(format(int(cell), "X") for cell in row)
            for row in self.grid.cells
        ]


def generate_maze(
    config,
    generation_steps: list[tuple[Point, Point]] | None = None,
) -> Grid:
    """Compatibility adapter for the application's configuration object."""
    generator = MazeGenerator(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit=config.exit,
        perfect=config.is_perfect,
        seed=config.seed,
        algorithm=getattr(config, "algorithm", "dfs"),
    )
    maze = generator.generate()
    if generation_steps is not None:
        generation_steps.extend(generator.generation_steps)
    return maze
