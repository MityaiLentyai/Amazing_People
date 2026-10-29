from enum import IntFlag
from file_input import Config
from dataclasses import dataclass


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


def parse_output(config: Config, file_name: str):
    start = Point(*config.entry)
    end = Point(*config.exit)
    current_grid = Grid(
        config.width,
        config.height,
        start,
        end,
        config.is_perfect
    )

    # TODO: REPLACE F's With a real maze that we will get
    with open(file_name, "w") as file:
        for row in range(current_grid.height):
            for letter in range(current_grid.width):
                file.write(format(int(current_grid.cells[row][letter]), "X"))
            file.write("\n")

    # TODO: BLANK LINE, FOOTER, SHORTEST PATH