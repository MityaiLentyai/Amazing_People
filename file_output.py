# from mazegen import MazeGenerator
from file_input import Grid, Config


def parse_output(config: Config | None, file_name: str):
    my_grid = Grid(config.width, config.height, config.entry, config.exit,
                   config.is_perfect)
    with open(file_name, "a") as file:
        file.write("Now the file has more content!\n")
