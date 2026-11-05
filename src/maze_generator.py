from collections.abc import Iterable
from dataclasses import dataclass
from enum import IntFlag

from .file_input import Config


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

    def reserve_cells(self, points: Iterable[Point]) -> None:
        cells = set(points)
        if any(not self.is_inside(point) for point in cells):
            raise ValueError("Reserved cells must be inside the grid")
        if self.start in cells or self.end in cells:
            raise ValueError("Entry and exit cells cannot be reserved")

        self.reserved_cells.update(cells)
        for point in cells:
            self.cells[point.y][point.x] = Wall.ALL

    def open_passage(self, point1: Point, point2: Point) -> bool:
        """Open a shared wall between adjacent playable cells."""
        if not self.is_playable(point1) or not self.is_playable(point2):
            return False

        directions = {
            (0, -1): (Wall.NORTH, Wall.SOUTH),
            (1, 0): (Wall.EAST, Wall.WEST),
            (0, 1): (Wall.SOUTH, Wall.NORTH),
            (-1, 0): (Wall.WEST, Wall.EAST),
        }
        direction = (point2.x - point1.x, point2.y - point1.y)
        walls = directions.get(direction)
        if walls is None:
            return False

        wall1, wall2 = walls
        self.cells[point1.y][point1.x] &= ~wall1
        self.cells[point2.y][point2.x] &= ~wall2
        return True

# Можно потом подкрутить чтобы оно красивее было, либо если баговать будет на определённых размерах
DIGIT_FOUR: tuple[tuple[int, ...], ...] = (
    (1, 0, 1),
    (1, 0, 1),
    (1, 1, 1),
    (0, 0, 1),
    (0, 0, 1),
)

DIGIT_TWO: tuple[tuple[int, ...], ...] = (
    (1, 1, 1),
    (0, 0, 1),
    (1, 1, 1),
    (1, 0, 0),
    (1, 1, 1),
)

DIGIT_GAP = 1  # Типа энв вариабла которую можно подкрутить в зависимости от размера мейза/Экрана
PATTERN_42_WIDTH = len(DIGIT_FOUR[0]) + DIGIT_GAP + len(DIGIT_TWO[0])
PATTERN_42_HEIGHT = len(DIGIT_FOUR)


def cells_from_bitmap(
        bitmap: tuple[tuple[int, ...], ...],
        origin: Point,
) -> set[Point]:
    cells: set[Point] = set()
    for dy, row in enumerate(bitmap):
        for dx, bit in enumerate(row):
            if bit:
                cells.add(Point(origin.x + dx, origin.y + dy))
    return cells


def pattern_42_origin(width: int, height: int) -> Point:
    return Point(
        (width - PATTERN_42_WIDTH) // 2,
        (height - PATTERN_42_HEIGHT) // 2,
    )


def pattern_42_candidate_origins(width: int, height: int) -> list[Point]:
    """
    Тут квадрат 7х5 который нужен для нашей 42, его резервируем под дальнейший
    движ
    """
    max_x = width - PATTERN_42_WIDTH
    max_y = height - PATTERN_42_HEIGHT
    mid_x = max_x // 2
    mid_y = max_y // 2

    candidates = [
        Point(mid_x, mid_y),
        Point(0, mid_y),
        Point(max_x, mid_y),
        Point(mid_x, 0),
        Point(mid_x, max_y),
        Point(0, 0),
        Point(max_x, 0),
        Point(0, max_y),
        Point(max_x, max_y),
    ]

    seen: set[Point] = set()
    unique: list[Point] = []
    for origin in candidates:
        if origin not in seen:
            seen.add(origin)
            unique.append(origin)
    return unique


def pattern_42_cells(origin: Point) -> set[Point]:
    four = cells_from_bitmap(DIGIT_FOUR, origin)
    two = cells_from_bitmap(
        DIGIT_TWO,
        Point(origin.x + len(DIGIT_FOUR[0]) + DIGIT_GAP, origin.y),
    )
    return four | two


def get_42_cells(
        width: int,
        height: int,
        start: Point | None = None,
        end: Point | None = None,
) -> set[Point] | None:
    if width < PATTERN_42_WIDTH or height < PATTERN_42_HEIGHT:
        print(
            f"Maze {width}x{height} is too small for the '42' pattern "
            f"(needs at least {PATTERN_42_WIDTH}x{PATTERN_42_HEIGHT}); "
            f"omitting it."
        )
        return None

    # Стараемся сдвинуть 42 если вход/выход на них. Если не вышло то скипуем 42
    forbidden = {p for p in (start, end) if p is not None}
    preferred = pattern_42_origin(width, height)

    for origin in pattern_42_candidate_origins(width, height):
        cells = pattern_42_cells(origin)
        if cells & forbidden:
            continue
        if origin != preferred:
            print(
                f"'42' pattern shifted to ({origin.x},{origin.y}) "
                f"to keep entry/exit free."
            )
        return cells

    print(
        "Cannot place the '42' pattern without covering entry/exit; "
        "omitting it."
    )
    return None


def generate_maze(config: Config):
    grid = Grid(
        width=config.width,
        height=config.height,
        start=Point(x=config.entry[0], y=config.entry[1]),
        end=Point(x=config.exit[0], y=config.exit[1]),
        perfect=config.is_perfect,
    )

    from .dfs import MazeGenerator

    maze = MazeGenerator(grid, seed=config.seed)
    maze.generate()
    # Tests potom udalit nahuy
    # print(f"{len(maze.visited) == maze.grid.width * maze.grid.height}")
    # pathfinder = BFS(grid)
    # path = pathfinder.find_path()
    # print(path)
    return grid
