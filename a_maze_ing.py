import sys

from mazegen import MazeGenerator

from src.file_input import ConfigError, parse_input
from src.file_output import parse_output
from src.visualizer import MazeRenderer


def main() -> int:
    """Run the application and return a process exit status."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt\n")
        return 1

    try:
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
        if path is None:
            print("Error: no valid path between entry and exit")
            return 1
        parse_output(config.output, maze.directions, grid)
        MazeRenderer.from_generator(maze, config.output).run()
        return 0
    except (ConfigError, OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
