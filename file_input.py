import sys
from pydantic import BaseModel, Field, model_validator, field_validator
from enum import IntFlag
from dataclasses import dataclass


@dataclass
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
            [Wall.NONE for _ in range(width)]
            for _ in range(height)
        ]


class Config(BaseModel):
    width: int = Field(ge=1, alias="WIDTH")
    height: int = Field(ge=1, alias="HEIGHT")
    entry: Point = Field(alias="ENTRY")
    exit: Point = Field(alias="EXIT")
    output: str = Field(alias="OUTPUT_FILE")
    is_perfect: bool = Field(default=False, alias="PERFECT")

    @model_validator(mode="after")
    def entry_validator(self):
        if not (0 <= self.entry.x < self.width):
            raise ValueError("Entry point X is outside the maze")

        if not (0 <= self.entry.y < self.height):
            raise ValueError("Entry point Y is outside the maze")

        return self

    @model_validator(mode="after")
    def exit_validator(self):

        if not (0 <= self.exit.x < self.width):
            raise ValueError("Exit point X is outside the maze")

        if not (0 <= self.exit.y < self.height):
            raise ValueError("Exit point Y is outside the maze")

        return self

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_coordinates(cls, value):
        if isinstance(value, str):
            x, y = value.split(",")
            return int(x), int(y)
        return value


def parse_input(config_name: str) -> Config | None:
    config = {}
    try:
        with open(config_name, "r") as file:
            for line in file:
                parsed_line = line.split("#")[0].strip()
                if "=" in parsed_line:
                    key, value = parsed_line.split("=", 1)
                    # print(key,value)
                    config.update({key: value})
        config = Config(**config)
        print(
            config)
        return config

    # Now config is not a dict but a Pydantic Config object.
    # you can access it with print(config.field)
    except FileNotFoundError as e:
        print(f"File {config_name} not found, please make sure it exists and "
              f"try again.")

    except PermissionError as e:
        print(f"Not enough access rights to either {config_name} or "
              f"{sys.argv[0]}\nPlease update the rights and try again\n"
              f"Exiting now xDD")
