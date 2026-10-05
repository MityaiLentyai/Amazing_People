from parser import Config, parse_input
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt\nExiting now XD")
        sys.exit(1)

    config = parse_input(sys.argv[1])


if __name__ == "__main__":
    main()
