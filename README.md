*This project has been created as part of the 42 curriculum by bdubovik, tmalyshi.*

# A-Maze-ing

## Description

A-Maze-ing is a Python maze generator, solver and MiniLibX visualizer. The
application reads one configuration file, generates a connected maze, writes
it in the hexadecimal format required by the 42 subject, finds a shortest
route between the entry and exit, and displays the result.

The project supports both subject modes:

- **Perfect maze** (`PERFECT=True`): the playable cells form a spanning tree,
  so there is exactly one route between any two playable cells.
- **Playable board** (`PERFECT=False`): additional passages create loops,
  corners and the centre remain reachable, and dead ends are reduced so the
  result can be used as a Pac-Man-like board.

The generator also reserves a fully closed `42` pattern whenever the grid is
large enough and a valid placement is possible. Small grids may not contain
the pattern; the program reports that situation instead of producing an
invalid placement.

## Features

- Deterministic generation with an optional integer seed.
- Two generation algorithms: iterative depth-first search (DFS) and randomized
  Prim.
- Perfect and non-perfect maze modes.
- Validation of dimensions, coordinates, required configuration keys and
  algorithm names.
- Breadth-first search (BFS) for a shortest entry-to-exit path.
- Subject-compliant hexadecimal wall encoding and solution footer.
- MiniLibX rendering with visible walls, entry, exit, solution and `42`
  pattern.
- Animated replay of the passages opened during generation.
- Runtime controls for regeneration, algorithm selection, path visibility,
  wall colours and quitting.
- `maze_analyzer.py` for checking wall coherence, connectivity, loops and
  dead ends.
- A standalone `mazegen` package that can be built and reused independently.

## Requirements

- Python 3.10 or newer.
- `uv` (recommended) or an equivalent Python package workflow.
- A Linux graphical environment with MiniLibX support to run the visualizer.
  The bundled `libmlx.so` wheel is not supported by native Windows. On WSL,
  configure a working X11/Wayland display before launching the application.

The project is type-checked with mypy and follows flake8 rules.

## Instructions

Run all commands from the repository root.

### Install

```sh
uv sync
```

This installs the project dependencies, including Pydantic for configuration
validation and the bundled MiniLibX wheel for development and display.

### Run the application

The required command-line interface accepts exactly one argument:

```sh
uv run python a_maze_ing.py config.txt
```

With an already prepared environment, the equivalent command is:

```sh
python3 a_maze_ing.py config.txt
```

The application validates the configuration, generates and writes the maze,
then opens the visualizer. Invalid arguments, missing files, malformed values,
impossible coordinates and runtime resource errors are reported as readable
messages and return a non-zero status.

Run the static checks used during development:

```sh
uv run flake8 .
uv run mypy . --warn-return-any --warn-unused-ignores \
  --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

### Build the reusable package

Build a wheel at the repository root:

```sh
uv build --wheel -o .
```

The resulting `mazegen-*.whl` can be installed into another environment:

```sh
python3 -m pip install mazegen-*.whl
```
### Using the Makefile

The project provides a Makefile to simplify installation, execution, debugging, and code quality checks. All commands should be executed from the root directory of the repository.

| Command | Description |
|---|---|
| `make install` | Installs and synchronizes project dependencies using `uv sync`. |
| `make run` | Runs A-Maze-ing using `config.txt` as the configuration file. |
| `make debug` | Runs the application with Python's built-in debugger (`pdb`). |
| `make lint` | Checks code style with `flake8` and performs type checking with `mypy`. |
| `make lint-strict` | Performs stricter type checking using `mypy --strict` alongside `flake8`. |
| `make clean` | Removes Python `__pycache__` directories and the `.mypy_cache` directory. |

**Installation and execution:**

```bash
make install
make run
```

**Debugging:**

```bash
make debug
```

**Code quality checks:**

```bash
make lint
make lint-strict
```

**Cleaning generated cache files:**

```bash
make clean
```

The Makefile's `run` and `debug` targets use `config.txt` by default. To run the application with a different configuration file, use the direct execution command and provide the desired filename.

## Configuration file

The repository includes `config.txt`. Use one `KEY=VALUE` pair per line.
Lines beginning with `#` and trailing `#` comments are ignored. Keys are
case-sensitive. Coordinates are zero-based and use the `x,y` format.

| Key | Required | Meaning | Example |
| --- | --- | --- | --- |
| `WIDTH` | Yes | Number of cells horizontally; must be at least `1`. | `WIDTH=20` |
| `HEIGHT` | Yes | Number of cells vertically; must be at least `1`. | `HEIGHT=10` |
| `ENTRY` | Yes | Entry cell `(x,y)`, inside the grid. | `ENTRY=0,0` |
| `EXIT` | Yes | Exit cell `(x,y)`, inside the grid and different from entry. | `EXIT=19,8` |
| `OUTPUT_FILE` | Yes | File receiving the generated maze. | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Yes | `True` for a perfect maze, `False` for a playable board. | `PERFECT=False` |
| `ALGORITHM` | No | `dfs` or `prim`; defaults to `dfs`. | `ALGORITHM=dfs` |
| `SEED` | No | Integer used for reproducible random choices. | `SEED=1` |

Example:

```text
WIDTH=20
HEIGHT=10
ENTRY=0,0
EXIT=19,8
OUTPUT_FILE=maze.txt
PERFECT=False
ALGORITHM=dfs
SEED=1
```

If `SEED` is omitted, generation is non-deterministic. Pressing `R` generates
a new maze with an unused seed and writes the new output to the same path; it
does not modify the configuration file.

## Maze and output requirements

The generator enforces the requirements from `amazeing.pdf`:

- every cell has four coherent cardinal wall flags;
- external borders remain closed;
- entry and exit are distinct, valid cells connected to the playable region;
- all non-reserved playable cells are connected;
- no open area is wider than the subject's allowed `3 x 2` / `2 x 3`
  corridors;
- the `42` pattern consists of fully closed cells where placement is possible;
- perfect mode has no loops;
- non-perfect mode has at least two independent routes, reachable corners and
  centre, and only a small number of real dead ends.

`src/maze_analyzer.py` can inspect a generated file:

```sh
uv run python src/maze_analyzer.py maze.txt
```

For the no-dead-end bonus check, use:

```sh
uv run python src/maze_analyzer.py maze.txt --max-dead-ends 0
```

## Output format

The output file contains:

1. One uppercase hexadecimal digit for every cell, one row per line.
2. One empty line.
3. The entry coordinates.
4. The exit coordinates.
5. The shortest path as `N`, `E`, `S` and `W`.

Every line ends with `\n`. A wall bit set to `1` means that the wall is
closed:

| Bit | Direction |
| --- | --- |
| `0` (least significant) | North |
| `1` | East |
| `2` | South |
| `3` | West |

For example, `A` is binary `1010`, so its east and west walls are closed.

## Visualizer controls

The visualizer first replays the generation animation and then displays the
shortest path when path display is enabled.

| Key | Action |
| --- | --- |
| `1` or `D` | Select DFS and regenerate. |
| `2` or `A` | Select randomized Prim and regenerate. |
| `R` | Generate and save another maze. |
| `P` | Show or hide the shortest path. |
| `C` | Cycle wall colours. |
| `Q` or `Escape` | Close the window. |

## Algorithm choice

The default algorithm is the iterative DFS backtracker. Starting at the entry,
it chooses an unvisited playable neighbour, opens the shared wall, and
backtracks when no unvisited neighbour remains. This naturally produces a
connected spanning tree, making it a good fit for `PERFECT=True`: it is simple,
memory-efficient and guarantees one route between cells before any optional
post-processing.

Randomized Prim is provided as an alternative. It grows the maze from a
frontier of neighbouring cells and generally produces a different visual
distribution while preserving the same connectivity guarantees. The seed
controls all random choices, so both algorithms are reproducible.

For non-perfect mode, post-processing opens carefully selected passages to
create independent loops while preserving connectivity, the `42` pattern and
the corridor-width constraint. BFS is used to solve the maze because every
cell-to-cell move has the same cost; therefore the first route found by BFS is
shortest.

## Reusable `mazegen` package

The reusable library is in `src/mazegen/` and is exposed by the
`mazegen-*.whl` package. Its public entry point is `MazeGenerator`; it does not
depend on the application configuration parser, file writer or visualizer.

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

print(grid.cells)          # generated wall grid
print(maze.path)           # shortest route as Point objects
print(maze.directions)     # route as N/E/S/W
print(maze.to_hex_rows())  # subject-compatible rows

maze.regenerate(seed=44)
```

`width` and `height` must be positive. `entry` and `exit` may be `(x, y)`
tuples or `Point` objects and must be different and inside the grid.
`algorithm` is either `"dfs"` or `"prim"`. The returned `Grid` exposes
`cells`, `start`, `end`, `reserved_cells`, `is_open_passage()` and
`iter_playable_cells()`. `MazeGenerator.solve()` recalculates the cached
solution; `regenerate()` creates a new grid and solution.

Short package-specific documentation is also available in
[`src/mazegen/README.md`](src/mazegen/README.md).

## Project structure

```text
.
├── a_maze_ing.py              # Required application entry point
├── amazeing.pdf               # A-Maze-ing subject, version 2.3
├── config.txt                 # Default configuration
├── maze.txt                   # Example output
├── mazegen-*.whl              # Reusable package artifact
├── LICENSE.md                 # MIT license
├── pyproject.toml             # Dependencies and build configuration
├── uv.lock                    # Locked dependency versions
├── src/
│   ├── mazegen/               # Reusable generation library
│   │   ├── maze_generator.py  # Public API and grid model
│   │   ├── dfs.py             # DFS generator
│   │   ├── primm.py           # Prim generator
│   │   ├── pattern_42.py      # 42 placement
│   │   ├── post_processing.py # Non-perfect maze processing
│   │   └── solver.py          # BFS shortest-path solver
│   ├── file_input.py          # Configuration parser and validation
│   ├── file_output.py         # Output serialization
│   ├── maze_analyzer.py       # Output validation utility
│   └── visualizer.py          # MiniLibX renderer and controls
```

## Team and project management

- **bdubovik:** visualization, BFS solving, DFS generation and reusable
  package integration.
- **tmalyshi:** Prim generation, configuration input, output serialization and
  `42` pattern processing.

The initial plan was to implement a compliant generator, add a MiniLibX
display, and package the generation logic for reuse. During implementation,
the plan was extended with a second generation algorithm, animated generation,
seed-based regeneration and `maze_analyzer.py` so that perfect and playable
requirements could be checked quantitatively.

The separation between generation, solving, serialization and rendering worked
well and made the package reusable. A future improvement would be to use a platform-neutral display backend or
provide a terminal renderer so the application is easier to use outside Linux.

Development tools included PyCharm, VS Code, `uv`, Git, GitHub, MiniLibX,
Pydantic, flake8 and mypy.

## Resources and AI use

- [`amazeing.pdf`](amazeing.pdf) — official A-Maze-ing subject, version 2.3.
- [Python `collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque)
  — queue used by BFS.
- [Python `random`](https://docs.python.org/3/library/random.html) — seeded
  random generation.
- [MiniLibX documentation](https://harm-smits.github.io/42docs/libs/minilibx/getting_started.html)
  — windows, images and event hooks.
- [Pydantic documentation](https://docs.pydantic.dev/) — configuration
  validation.

AI was used as a development assistant for reviewing the subject requirements,
checking edge cases in configuration and output handling, improving the
MiniLibX animation and control documentation, and drafting this README. All
generated suggestions were inspected and adapted to the project.

## License

This project is distributed under the MIT License. See
[`LICENSE.md`](LICENSE.md).
