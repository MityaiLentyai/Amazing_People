# mazegen

`mazegen` is a dependency-free Python library for generating and solving
connected mazes.

## Install

Build and install the package from the project root:

```sh
uv build --wheel -o .
python -m pip install mazegen-*.whl
```

## Usage

```python
from mazegen import MazeGenerator

maze = MazeGenerator(
    width=20,
    height=15,
    entry=(0, 0),
    exit=(19, 14),
    perfect=True,
    seed=43,
    algorithm="dfs",
)
grid = maze.generate()

print(maze.path)       # shortest route as Point objects
print(maze.directions) # N, E, S, W directions
print(maze.to_hex_rows())

grid = maze.regenerate(seed=44)
```

`width` and `height` must be positive integers. `entry` and `exit` accept
`(x, y)` tuples or `Point` objects, must be different, and must be inside the
grid. `perfect=True` generates a spanning tree; `perfect=False` adds passages
and loops. `seed` makes generation reproducible. Supported algorithms are
`"dfs"` and `"prim"`.

The returned `Grid` exposes `cells`, `start`, `end`, `reserved_cells`,
`is_open_passage()`, and `iter_playable_cells()`. `MazeGenerator.path` and
`MazeGenerator.directions` contain the cached shortest solution;
`solve()` recalculates it.

## License

MIT License. See `LICENSE.md`.
