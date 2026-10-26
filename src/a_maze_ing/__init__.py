from a_maze_ing.file_input import parse_input
from a_maze_ing.file_output import parse_output
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run a-maze-ing config.txt\nExiting now XD")
        sys.exit(1)

    config = parse_input(sys.argv[1])

    parse_output("output.txt")


if __name__ == "__main__":
    main()
