"""Reusable, dependency-free maze generation and solving.

Example:

    from mazegen import MazeGenerator

    maze = MazeGenerator(20, 15, (0, 0), (19, 14), seed=43, algorithm="prim")
    grid = maze.generate()
    print(maze.directions)
    maze.regenerate()
"""

from .maze_generator import (
    ALGORITHMS,
    Grid,
    MazeGenerator,
    Point,
    Wall,
    generate_maze,
)
from .solver import BFS

__version__ = "0.1.0"

__all__ = [
    "ALGORITHMS",
    "BFS",
    "Grid",
    "MazeGenerator",
    "Point",
    "Wall",
    "__version__",
    "generate_maze",
]
