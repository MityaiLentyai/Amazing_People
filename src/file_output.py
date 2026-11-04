from .file_input import Config
from .maze_generator import Point, Grid


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

        file.write("\n")

        file.write(f"{start.x},{start.y}\n")

        file.write(f"{end.x},{end.y}\n")

        file.write("\n")
        file.write("SHORTEST PATH WILL GO HERE")  # TODO: SHORTEST PATH
