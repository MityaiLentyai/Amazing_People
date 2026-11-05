from collections import deque
from dataclasses import dataclass
from enum import IntFlag
import random

from .file_input import Config

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


@dataclass(frozen=True)  # to be able to put it into sets later
class Point:
    x: int
    y: int


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


class Wall(IntFlag):
    """Enum for translating wall to bits"""
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

        self.cells = [
            [Wall.ALL for _ in range(width)]
            for _ in range(height)
        ]


class MazeGenerator:
    def __init__(self, grid: Grid, seed: int | None = None):
        self.grid = grid
        self.rng = random.Random(seed)
        self.visited = set()
        self.stack = []

    def get_neighbors(self, point: Point) -> list[Point]:
        neigs = []
        if point.x > 0:
            neigs.append(Point(x=point.x - 1, y=point.y))
        if point.x < self.grid.width - 1:
            neigs.append(Point(x=point.x + 1, y=point.y))
        if point.y > 0:
            neigs.append(Point(x=point.x, y=point.y - 1))
        if point.y < self.grid.height - 1:
            neigs.append(Point(x=point.x, y=point.y + 1))
        return neigs

    def get_unvisited_neighbors(self, point: Point) -> list[Point]:
        neigs = self.get_neighbors(point)
        return [neig for neig in neigs if neig not in self.visited]

    def open_walls(self, point1: Point, point2: Point):
        if point2.x == point1.x + 1 and point2.y == point1.y:
            self.grid.cells[point1.y][point1.x] &= ~Wall.EAST
            self.grid.cells[point2.y][point2.x] &= ~Wall.WEST
        elif point2.x + 1 == point1.x and point2.y == point1.y:
            self.grid.cells[point1.y][point1.x] &= ~Wall.WEST
            self.grid.cells[point2.y][point2.x] &= ~Wall.EAST
        elif point2.x == point1.x and point2.y == point1.y + 1:
            self.grid.cells[point1.y][point1.x] &= ~Wall.SOUTH
            self.grid.cells[point2.y][point2.x] &= ~Wall.NORTH
        elif point2.x == point1.x and point2.y + 1 == point1.y:
            self.grid.cells[point1.y][point1.x] &= ~Wall.NORTH
            self.grid.cells[point2.y][point2.x] &= ~Wall.SOUTH

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
                self.open_walls(current, rand)

        if not self.grid.perfect:
            self.remove_dead_ends()
            self.check_corners_center()
            self.add_extra_passages()

    def count_open_neighbors(self, point: Point) -> int:
        count = 0
        cell = self.grid.cells[point.y][point.x]
        if not (cell & Wall.NORTH):
            count += 1
        if not (cell & Wall.SOUTH):
            count += 1
        if not (cell & Wall.EAST):
            count += 1
        if not (cell & Wall.WEST):
            count += 1
        return count

    def get_closed_neighbors(self, point: Point):
        neighbours = self.get_neighbors(point)
        closed = []
        cell = self.grid.cells[point.y][point.x]
        for neighbour in neighbours:
            if neighbour.x == point.x + 1:
                if cell & Wall.EAST and self.grid.cells[neighbour.y][
                    neighbour.x] & Wall.WEST:
                    closed.append(neighbour)

            if neighbour.x + 1 == point.x:
                if cell & Wall.WEST and self.grid.cells[neighbour.y][
                    neighbour.x] & Wall.EAST:
                    closed.append(neighbour)

            if neighbour.y == point.y + 1:
                if cell & Wall.SOUTH and self.grid.cells[neighbour.y][
                    neighbour.x] & Wall.NORTH:
                    closed.append(neighbour)

            if neighbour.y + 1 == point.y:
                if cell & Wall.NORTH and self.grid.cells[neighbour.y][
                    neighbour.x] & Wall.SOUTH:
                    closed.append(neighbour)
        return closed

    def remove_dead_ends(self) -> None:
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                tmp = Point(x, y)
                neibs_count = self.count_open_neighbors(tmp)
                if neibs_count == 1:
                    possibilities = self.get_closed_neighbors(tmp)
                    if possibilities:
                        r = self.rng.choice(possibilities)
                        self.open_walls(tmp, r)

    def add_extra_passages(self) -> None:
        is_option = True
        while self.count_loops() < 2 and is_option:
            is_option = False
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    tmp = Point(x, y)
                    possibilities = self.get_closed_neighbors(tmp)
                    if possibilities:
                        r = self.rng.choice(possibilities)
                        self.open_walls(tmp, r)
                        if self.count_loops() >= 2:
                            return
                        is_option = True
                        break
                if is_option:
                    break

    def count_loops(self):
        v = self.grid.width * self.grid.height
        e = 0
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                e += self.count_open_neighbors(Point(x, y))
        return e // 2 - v + 1

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
            while self.count_open_neighbors(c) < 2:
                open_neibs = self.get_closed_neighbors(c)
                if open_neibs:
                    r = self.rng.choice(open_neibs)
                    self.open_walls(c, r)
                else:
                    break


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


def generate_maze(config: Config):
    grid = Grid(
        width=config.width,
        height=config.height,
        start=Point(x=config.entry[0], y=config.entry[1]),
        end=Point(x=config.exit[0], y=config.exit[1]),
        perfect=config.is_perfect,
    )

    maze = MazeGenerator(grid, seed=config.seed)
    maze.generate()
    # Tests potom udalit nahuy
    # print(f"{len(maze.visited) == maze.grid.width * maze.grid.height}")
    # pathfinder = BFS(grid)
    # path = pathfinder.find_path()
    # print(path)
    return grid
