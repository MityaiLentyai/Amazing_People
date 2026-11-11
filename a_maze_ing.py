import random
import sys
from collections.abc import Callable

from src.bfs import BFS
from src.file_input import Config, parse_input
from src.file_output import parse_output
from src.maze_generator import Grid, Point, generate_maze
from src.visualizer import MazeRenderer


def make_regenerator(
    config: Config,
) -> Callable[[], tuple[Grid, list[Point], list[tuple[Point, Point]]]]:
    used_seeds = {config.seed} if config.seed is not None else set()
    seed_source = random.SystemRandom()
    current_config = config

    def regenerate() -> tuple[Grid, list[Point], list[tuple[Point, Point]]]:
        nonlocal current_config
        seed = seed_source.randrange(0, 2**32)
        while seed in used_seeds:
            seed = seed_source.randrange(0, 2**32)
        used_seeds.add(seed)
        current_config = current_config.model_copy(update={"seed": seed})

        generation_steps: list[tuple[Point, Point]] = []
        maze = generate_maze(current_config, generation_steps)
        bfs = BFS(maze)
        path = bfs.find_path()
        if path is None:
            raise RuntimeError("Regenerated maze has no path from entry to exit")

        parse_output(current_config.output, bfs.get_direction(path), maze)
        return maze, path, generation_steps

    return regenerate


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt\n")
        sys.exit(1)

    config = parse_input(sys.argv[1])

    generation_steps: list[tuple[Point, Point]] = []
    maze = generate_maze(config, generation_steps)

    bfs = BFS(maze)
    path = bfs.find_path()
    if path is not None:
        shortest_p = bfs.get_direction(path)
        parse_output(config.output, shortest_p, maze)
        render = MazeRenderer(
            maze,
            path,
            make_regenerator(config),
            generation_steps=generation_steps,
        )
        render.run()
    else:
        print("Error, no path")


if __name__ == "__main__":
    main()
