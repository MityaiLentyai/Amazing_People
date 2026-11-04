from src.file_input import parse_input
from src.file_output import parse_output
import sys
from src.maze_generator import generate_maze, BFS


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt\n")
        sys.exit(1)

    config = parse_input(sys.argv[1])

    maze = generate_maze(config)

    bfs = BFS(maze)
    shortest_p = bfs.get_direction(bfs.find_path())
    parse_output(config, shortest_p, maze)


if __name__ == "__main__":
    main()
