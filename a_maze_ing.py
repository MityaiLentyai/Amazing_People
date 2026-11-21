import sys

from src.file_input import parse_input
from src.file_output import parse_output
from mazegen import MazeGenerator
from src.visualizer import MazeRenderer


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt\n")
        sys.exit(1)

    config = parse_input(sys.argv[1])

    maze = MazeGenerator(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit=config.exit,
        perfect=config.is_perfect,
        seed=config.seed,
        algorithm=config.algorithm,
    )
    grid = maze.generate()
    path = maze.path
    if path is not None:
        parse_output(config.output, maze.directions, grid)
        MazeRenderer.from_generator(maze, config.output).run()
    else:
        print("Error, no path")


if __name__ == "__main__":
    main()
