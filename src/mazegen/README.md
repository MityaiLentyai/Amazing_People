# mazegen

`mazegen` is a dependency-free Python library for generating and solving
connected mazes.

## Install

### From the repository source

If the complete repository is available, build and install the package from
the project root:

```sh
uv build --wheel -o .
uv pip install ./mazegen-0.1.0-py3-none-any.whl
```

You can also let `uv` build and install the package directly:

```sh
uv pip install .
```

### From an existing wheel

With an existing `mazegen-*.whl` file, no `src/mazegen` source directory is
needed:

```sh
uv pip install ./mazegen-0.1.0-py3-none-any.whl
```

The conventional `pip` form is also supported:

```sh
python -m pip install ./mazegen-0.1.0-py3-none-any.whl
```

The wheel is usable on supported Python versions from 3.10 onwards. It contains
only the reusable `mazegen` library and has no third-party runtime
dependencies.

This package is not the complete A-Maze-ing application. The wheel does not
contain `a_maze_ing.py`, `config.txt`, the visualizer or MiniLibX. Therefore,
installing only the wheel cannot start the full project. Keep the application
source or distribute a separate application entry point to run the visual
application.

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
