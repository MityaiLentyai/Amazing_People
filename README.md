*This project has been created as part of the 42 curriculum by bdubovik and tmalyshi.*

# A-Maze-ing

## Description

A-Maze-ing is a Python maze generator and visualizer based on the 42 A-Maze-ing
subject (version 2.3). It reads maze dimensions, entry and exit coordinates,
generation mode, and an optional random seed from a configuration file. It
generates the maze, finds a shortest route from entry to exit, writes the maze
and route to a text file, and displays an animated graphical representation.

The implementation uses a depth-first search (DFS) backtracker to carve
connected passages. In perfect mode the carved playable cells form a spanning
tree; in non-perfect mode the generator opens additional passages to create
loops and tries to reduce dead ends. A closed-cell `42` pattern is placed when
the grid can accommodate it without blocking the entry, exit, or connectivity.

## Features

- Seeded generation for repeatable mazes.
- Perfect and non-perfect generation modes.
- A reserved, fully walled `42` pattern when the dimensions and layout allow it.
- Breadth-first search (BFS) to find a shortest path from entry to exit.
- Text output containing hexadecimal wall flags, coordinates, and path directions.
- MiniLibX display with animated passage carving, entry/exit markers, and a
  shortest-path overlay.
- Clickable **New maze** and **Show path** / **Hide path** controls.
- Keyboard controls for path visibility, wall colors, regeneration, and exit.
- `src/maze_analyzer.py` to inspect output-file wall consistency, connectivity,
  loops, and dead ends.

## Requirements

- Python 3.10 or later, as required by the subject. This repository pins Python
  3.14 in `.python-version`.
- `uv` for the setup commands below; dependencies and the local MiniLibX wheel
  are declared in `pyproject.toml` and locked in `uv.lock`.
- A Linux graphical environment with a display supported by MiniLibX to run the
  visualizer. The bundled MiniLibX library uses `libmlx.so`, so the graphical
  application is not supported by this bundle on native Windows. WSL users need
  a working graphical display/forwarding setup.

## Instructions

Run the following commands from the repository root. Install `uv` first if it
is not already available:

```sh
uv sync
uv run python a_maze_ing.py config.txt
```

The equivalent command in an environment where dependencies are already
installed is:

```sh
python3 a_maze_ing.py config.txt
```

The program accepts exactly one command-line argument: the configuration file
path. It writes the maze to the path in `OUTPUT_FILE`; relative paths are
resolved from the current working directory. Running the program opens the
visualizer after generation and writing the initial maze.

### Configuration file

The repository includes `config.txt` as the default configuration. Use one
`KEY=VALUE` pair per line; lines beginning with `#` and trailing `#` comments
are ignored. Coordinates are zero-based `(x,y)` pairs. The parser accepts
coordinates written as `x,y`. The subject requires `WIDTH`, `HEIGHT`, `ENTRY`,
`EXIT`, `OUTPUT_FILE`, and `PERFECT`; the current parser defaults an omitted
`PERFECT` value to `False`. `SEED` is an optional project-specific setting.

| Key | Meaning | Example / default |
| --- | --- | --- |
| `WIDTH` | Number of cells horizontally; must be at least 1. | `WIDTH=10` |
| `HEIGHT` | Number of cells vertically; must be at least 1. | `HEIGHT=10` |
| `ENTRY` | Entry cell as `x,y`, within the grid. | `ENTRY=0,0` |
| `EXIT` | Exit cell as `x,y`, within the grid. | `EXIT=6,8` |
| `OUTPUT_FILE` | Destination for the generated maze and solution. | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Generate a perfect maze when `True`; defaults to `False` in the current parser. | `PERFECT=True` |
| `SEED` | Optional integer seed for repeatable generation. | `SEED=43` |

Example:

```text
WIDTH=10
HEIGHT=10
ENTRY=0,0
EXIT=6,8
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=43
```

For reproducible output, keep the same configuration and seed. If `SEED` is
omitted, Python's random generator chooses an unseeded sequence. Clicking **New
maze** (or pressing `R`) uses a fresh seed for the new maze; it saves that
maze and its solution to the same output path, but does not rewrite the
configuration file with the new seed.

### Maze output format

The output contains one uppercase hexadecimal digit for each cell, one row per
line. Each digit stores the closed-wall flags: bit 0 is North, bit 1 East, bit
2 South, and bit 3 West. A set bit means the wall is closed; a cleared bit
means the passage is open. For example, `A` (`1010` in binary) means the East
and West walls are closed.

After the rows, the file has a blank line followed by the entry coordinates,
exit coordinates, and shortest path on separate lines. The path consists of
`N`, `E`, `S`, and `W` direction letters. For example, the supplied `maze.txt`
uses this format.

### Visualizer controls

Passage openings are replayed as an animation. The path overlay appears after
the animation completes when path display is enabled.

| Input | Action |
| --- | --- |
| Click **New maze** or press `R` | Generate another maze and update the output file. |
| Click **Show path** / **Hide path** or press `P` | Toggle the shortest-path overlay. |
| Press `C` | Cycle through wall colors. |
| Press `Q` or `Escape` | Close the visualizer. |

## Algorithm choice

`src/dfs.py` implements an iterative depth-first backtracker: it starts at the
entry, chooses an unvisited playable neighbor, opens the shared wall, and
backtracks when no unvisited neighbor remains. This is a compact way to visit
every connected playable cell and, before non-perfect post-processing, carve
a spanning tree. The optional seed makes the same choices reproducible.

For `PERFECT=True`, the spanning-tree passages remain the generated maze. For
`PERFECT=False`, post-processing opens more passages, aims to keep the four
corners and center usable, reduces dead ends, and adds at least two independent
loops when the available cells permit it. The implementation uses BFS in
`src/bfs.py` because each grid move has equal cost; BFS returns a shortest
route in number of cell-to-cell moves.

## Reusing the generator

The generator API is available from the `src` Python package. Configure custom
dimensions, endpoints, mode, and seed with `Config`; `generate_maze` returns a
`Grid`, whose wall flags, endpoints, and reserved cells can be inspected. Use
`BFS` to obtain a shortest path as `Point` objects and `get_direction` to
convert it to the output's direction letters:

```python
from src.bfs import BFS
from src.file_input import Config
from src.maze_generator import generate_maze

config = Config(
    WIDTH=20,
    HEIGHT=15,
    ENTRY=(0, 0),
    EXIT=(19, 14),
    OUTPUT_FILE="maze.txt",
    PERFECT=True,
    SEED=43,
)
grid = generate_maze(config)
solver = BFS(grid)
path = solver.find_path()
if path is None:
    raise RuntimeError("No route from entry to exit")

directions = solver.get_direction(path)
print(grid.width, grid.height, grid.start, grid.end)
print("Shortest path:", "".join(directions))
print("Reserved cells:", grid.reserved_cells)
print("Wall flags at (0, 0):", grid.cells[0][0])
```

`src.dfs.MazeGenerator` is the generator class; the higher-level
`src.maze_generator.generate_maze` function creates the grid and applies the
`42`-pattern placement before invoking it. The project metadata names the
installable distribution `mazegen` and configures its Python module as `src`;
import the documented `src.*` modules rather than `mazegen`.

To rebuild the distribution from the project sources, use `uv build`. A wheel
is also included at the repository root. In a Python environment, install the
included distribution and its bundled MiniLibX dependency with:

```sh
python3 -m pip install ./mazegen-0.1.0-py3-none-any.whl ./libs/mlx-2.2-py3-none-any.whl
```

The bundled MiniLibX wheel targets Linux. After installation, import the
documented modules as `src.*`; the source modules and this README provide the
reusable API example and usage documentation.

## Project structure

```text
.
├── a_maze_ing.py                 # Required command-line entry point
├── amazeing.pdf                  # A-Maze-ing subject, version 2.3
├── config.txt                    # Default generation configuration
├── maze.txt                      # Example generated output
├── LICENSE.md                    # MIT license
├── .gitignore                    # Python/build artifacts and IDE files
├── .python-version               # Python 3.14 project pin
├── libs/
│   └── mlx-2.2-py3-none-any.whl  # Bundled MiniLibX Python package
├── mazegen-0.1.0-py3-none-any.whl
├── pyproject.toml                # Project and build configuration
├── uv.lock                       # Locked dependency versions
├── src/
│   ├── 42.py                     # Reserved-cell pattern placement
│   ├── bfs.py                    # Shortest-path search
│   ├── dfs.py                    # Depth-first maze generation
│   ├── file_input.py             # Configuration parsing and validation
│   ├── file_output.py            # Maze and solution serialization
│   ├── maze_analyzer.py          # Output-file analysis utility
│   ├── maze_generator.py         # Grid model and generation entry point
│   ├── primm.py                  # Not currently used by the generation flow
│   └── visualizer.py             # MiniLibX renderer and interactions
```

## Team and project management

- **bdubovik:** visualization, BFS, DFS, and the standalone module.
- **tmalyshi:** Prim's algorithm, input, output, and the `42` pattern.
- **Initial plan:** build a maze generator with MiniLibX visualization.
- **Plan changes:** the initial plan did not change.
- **Retrospective:** maze generation worked well; next time, we would
  choose a different visualization method.
- **Tools:** PyCharm, VS Code, `uv`, Git, and GitHub.

## Resources and AI use

- [A-Maze-ing subject (version 2.3)](amazeing.pdf) — requirements for the
  generator, output format, visualization, reusable package, and README.
- [MiniLibX getting started](https://harm-smits.github.io/42docs/libs/minilibx/getting_started.html)
  — windowing, image, and event-loop reference.
- [Python `collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque)
  — queue used by BFS.
- [Python `random`](https://docs.python.org/3/library/random.html) — seeded
  random choices for generation.
- [Pydantic documentation](https://docs.pydantic.dev/) — configuration model
  and validation library.

AI assistance was used to help develop the MiniLibX maze visualization,
generation-step recording and animation, project documentation.

## Current implementation notes

- The subject says the entry and exit must be different. The current
  configuration parser checks that both are inside the grid, but it does not
  explicitly reject matching coordinates.
- A `42` pattern needs at least a 7-by-5 grid and can still be omitted if no
  placement preserves the required cells and connectivity.
- The current project uses DFS; `src/primm.py` is not connected to the active
  generation flow. The project root does not currently include the subject's
  requested Makefile, so use the `uv` commands above.
- A graphical smoke test requires a Linux MiniLibX display. Headless unit tests
  can run without one.

## License

This project is distributed under the MIT License; see `LICENSE.md`.
