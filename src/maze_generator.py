from dataclasses import dataclass
from enum import IntFlag
import random

from .file_input import Config


@dataclass(frozen=True)  # to be able to put it into sets later
class Point:
    x: int
    y: int


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
    def __init__(self, grid: Grid):
        self.grid = grid
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
            self.grid.cells[point1.y][point1.x] &= ~Wall.NORTH
            self.grid.cells[point2.y][point2.x] &= ~Wall.SOUTH
        elif point2.x == point1.x and point2.y + 1 == point1.y:
            self.grid.cells[point1.y][point1.x] &= ~Wall.SOUTH
            self.grid.cells[point2.y][point2.x] &= ~Wall.NORTH

    def generate(self):
        self.visited.add(self.grid.start)
        self.stack.append(self.grid.start)
        while self.stack:
            current = self.stack[-1]
            neigbours = self.get_unvisited_neighbors(current)
            if not neigbours:
                self.stack.pop()
            else:
                rand = random.choice(neigbours)
                self.visited.add(rand)
                self.stack.append(rand)
                self.open_walls(current, rand)
    #
    # @staticmethod
    # def t(self):
    #     return len(self.visited) == self.grid.width * self.grid.height


def generate_maze(config: Config):
    grid = Grid(
        width=config.width,
        height=config.height,
        start=Point(x=config.entry[0], y=config.entry[1]),
        end=Point(x=config.exit[0], y=config.exit[1]),
        perfect=config.is_perfect,
    )

    maze = MazeGenerator(grid)
    maze.generate()
    print(f"{len(maze.visited) == maze.grid.width * maze.grid.height}")
    return grid
