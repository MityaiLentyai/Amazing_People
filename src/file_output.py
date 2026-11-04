from .maze_generator import Grid


def parse_output(file_name: str, shortest_path, maze: Grid):
    start = maze.start
    end = maze.end
    with open(file_name, "w") as file:
        for row in maze.cells:
            for cell in row:
                file.write(format(int(cell), "X"))
            file.write("\n")

        file.write("\n")

        file.write(f"{start.x},{start.y}\n")

        file.write(f"{end.x},{end.y}\n")

        if shortest_path is not None:
            file.write("".join(shortest_path))
