from .file_input import Config
from .maze_generator import Point, Grid


def parse_output(config: Config, shortest_path, maze : Grid):
    start = Point(*config.entry)
    end = Point(*config.exit)
    file_name = config.output
    with open(file_name, "w") as file:
        for row in maze.cells:
            for cell in row:
                file.write(format(int(cell), "X"))
            file.write("\n")

        file.write("\n")

        file.write(f"{start.x},{start.y}\n")

        file.write(f"{end.x},{end.y}\n")

        file.write("".join(shortest_path))
