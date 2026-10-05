import sys
from pydantic import BaseModel, Field, model_validator


class Config(BaseModel):
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    entry: tuple[int, int]
    exit: tuple[int, int]
    output: str
    is_perfect: bool = Field(default=False)

    @model_validator(mode="after")
    def entry_validator(self):

        x, y = self.entry

        if not (0 <= x < self.maze_width):
            raise ValueError("Entry point X is outside the maze")

        if not (0 <= y < self.maze_height):
            raise ValueError("Entry point Y is outside the maze")

        return self

    @model_validator(mode="after")
    def exit_validator(self):

        x, y = self.exit

        if not (0 <= x < self.maze_width):
            raise ValueError("Entry point X is outside the maze")

        if not (0 <= y < self.maze_height):
            raise ValueError("Entry point Y is outside the maze")

        return self


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt\nExiting now XD")
        sys.exit(1)

    config_name = sys.argv[1]
    try:
        with open(config_name, "r") as full_config_file:
            print(full_config_file)

    except FileNotFoundError as e:
        print(f"File {config_name} not found, please make sure it exists and "
              f"try again.")
    except PermissionError as e:
        print(f"'Not enough permissions to either {config_name} or "
              f"{sys_argv[0]}\nPlease update the rights and try again\n"
              f"Exiting now xDD")


if __name__ == "__main__":
    main()
