from src.file_input import parse_input
from src.file_output import parse_output
import sys

def main() -> None:

    def main() -> None:
        if len(sys.argv) != 2:
            print("Usage: python3 a_maze_ing.py config.txt\nExiting now XD")
            sys.exit(1)

        config = parse_input(sys.argv[1])

        parse_output(config, "output.txt")

    if __name__ == "__main__":
        main()


if __name__ == "__main__":
    main()
