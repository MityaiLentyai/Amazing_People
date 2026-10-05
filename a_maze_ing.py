import sys
import os
from pydantic import BaseModel, Field, model_validator, field_validator


class Config(BaseModel):
    width: int = Field(ge=1, alias="WIDTH")
    height: int = Field(ge=1, alias="HEIGHT")
    entry: tuple[int, int] = Field(alias="ENTRY")
    exit: tuple[int, int] = Field(alias="EXIT")
    output: str = Field(alias="OUTPUT_FILE")
    is_perfect: bool = Field(default=False, alias="PERFECT")

    @model_validator(mode="after")
    def entry_validator(self):

        x, y = self.entry

        if not (0 <= x < self.width):
            raise ValueError("Entry point X is outside the maze")

        if not (0 <= y < self.height):
            raise ValueError("Entry point Y is outside the maze")

        return self

    @model_validator(mode="after")
    def exit_validator(self):

        x, y = self.exit

        if not (0 <= x < self.width):
            raise ValueError("Exit point X is outside the maze")

        if not (0 <= y < self.height):
            raise ValueError("Exit point Y is outside the maze")

        return self

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_coordinates(cls, value):
        if isinstance(value, str):
            x, y = value.split(",")
            return int(x), int(y)
        return value

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt\nExiting now XD")
        sys.exit(1)

    config = {}
    try:
        with open(sys.argv[1], "r") as file:
            for line in file:
                parsed_line = line.split("#")[0].strip()
                if "=" in parsed_line:
                    key,value = parsed_line.split("=",1)
                    # print(key,value)
                    config.update({key:value})
        config = Config(**config)
        print(config) #TODO: Delete this print when parser is done
    except FileNotFoundError as e:
        print(f"File {sys.argv[1]} not found, please make sure it exists and "
              f"try again.")
    except PermissionError as e:
        print(f"Not enough access rights to either {sys.argv[1]} or "
              f"{sys_argv[0]}\nPlease update the rights and try again\n"
              f"Exiting now xDD")


if __name__ == "__main__":
    main()
