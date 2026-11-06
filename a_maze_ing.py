from src.file_input import parse_input
from src.file_output import parse_output
import sys
from src.bfs import BFS
from src.maze_generator import generate_maze
from src.visualizer import MazeRenderer

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt\n")
        sys.exit(1)

    config = parse_input(sys.argv[1])
    # from importlib import import_module # TODO: tester for 42, delete afterr
    # from src.maze_generator import Point
    #
    # glyph_42 = import_module("src.42")
    #
    # cells = glyph_42.get_42_cells(
    #     config.width,
    #     config.height,
    #     Point(*config.entry),
    #     Point(*config.exit),
    #     config.is_perfect,
    # )
    #
    # print("42 cells:", cells)
    # if cells is not None:
    #     print(
    #         "All normal cells connected:",
    #         glyph_42.playable_cells_are_connected(
    #             config.width,
    #             config.height,
    #             cells,
    #         ),
    #     )

    maze = generate_maze(config)

    bfs = BFS(maze)
    path = bfs.find_path()
    if path:
        shortest_p = bfs.get_direction(path)
        parse_output(config.output, shortest_p, maze)
        render = MazeRenderer(maze)
        render.run()
    else:
        print("Error, no path")


if __name__ == "__main__":
    main()
