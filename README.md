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
- A clean visualizer footer with keyboard-only controls.
- Fixed visualizer window dimensions and persistent keyboard legend.
- Live DFS/Prim algorithm selection while the visualizer is running.
- Keyboard controls for algorithm selection, path visibility, wall colors,
  regeneration, and exit.
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
`EXIT`, `OUTPUT_FILE`, and `PERFECT`; `PERFECT` is now mandatory and must be
`True` or `False`. `SEED` is an optional project-specific setting.

| Key | Meaning | Example / default |
| --- | --- | --- |
| `WIDTH` | Number of cells horizontally; must be at least 1. | `WIDTH=10` |
| `HEIGHT` | Number of cells vertically; must be at least 1. | `HEIGHT=10` |
| `ENTRY` | Entry cell as `x,y`, within the grid. | `ENTRY=0,0` |
| `EXIT` | Exit cell as `x,y`, within the grid. | `EXIT=6,8` |
| `OUTPUT_FILE` | Destination for the generated maze and solution. | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Generate a perfect maze when `True`; required. | `PERFECT=True` |
| `ALGORITHM` | Generation algorithm: depth-first search (`dfs`) or randomized Prim (`prim`); defaults to `dfs`. | `ALGORITHM=dfs` |
| `SEED` | Optional integer seed for repeatable generation. | `SEED=43` |

Example:

```text
WIDTH=10
HEIGHT=10
ENTRY=0,0
EXIT=6,8
OUTPUT_FILE=maze.txt
PERFECT=True
ALGORITHM=dfs
SEED=43
```

For reproducible output, keep the same configuration and seed. If `SEED` is
omitted, Python's random generator chooses an unseeded sequence. Pressing `R`
uses a fresh seed for the new maze; it saves that
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
| `1` or `D` | Switch to depth-first search (DFS) and regenerate. |
| `2` or `A` | Switch to randomized Prim or cycle to the next algorithm. |
| `R` | Generate another maze and update the output file. |
| `P` | Toggle the shortest-path overlay. |
| Press `C` | Cycle through wall colors. |
| Press `Q` or `Escape` | Close the visualizer. |

## Algorithm choice

`ALGORITHM=dfs` selects the iterative depth-first backtracker: it starts at the
entry, chooses an unvisited playable neighbor, opens the shared wall, and
backtracks when no unvisited neighbor remains. `ALGORITHM=prim` selects the
randomized Prim generator, which grows the maze from a frontier of adjacent
unvisited cells. Both algorithms visit every connected playable cell and carve
a spanning tree before non-perfect post-processing. The optional seed makes
the same choices reproducible.

For `PERFECT=True`, the spanning-tree passages remain the generated maze. For
`PERFECT=False`, post-processing opens more passages, aims to keep the four
corners and center usable, reduces dead ends, and adds at least two independent
loops when the available cells permit it. The implementation uses BFS in
`src/mazegen/solver.py` because each grid move has equal cost; BFS returns a shortest
route in number of cell-to-cell moves.

## Reusing the generator

The maze generator is a standalone Python library with no runtime dependencies.
Build the wheel with `uv build --wheel -o .`, then install it in the
project or another Python environment:

```sh
python -m pip install mazegen-*.whl
```

Then create a maze directly, without the application's configuration parser,
file output, or MiniLibX visualizer:

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
print("Shortest path:", "".join(maze.directions))
print("Path cells:", maze.path)
print("Wall flags at (0, 0):", grid.cells[0][0])
print("Hex rows:", maze.to_hex_rows())

# Create a new maze with a seed not used by this instance.
grid = maze.regenerate()
print("New seed:", maze.seed)
```

`width` and `height` are positive cell counts; `entry` and `exit` accept
`(x, y)` tuples or `Point` objects and must be inside the grid. Set `perfect`
to `False` for additional loops, pass an integer `seed` for repeatable output,
and choose `"dfs"` or `"prim"` with `algorithm`.

`generate()` returns a `Grid`. Inspect `grid.cells` for `Wall` flags,
`grid.start`/`grid.end` for endpoints, and `grid.reserved_cells` for the
optional `42` pattern. The generator stores the shortest route in `maze.path`
and its `N`/`E`/`S`/`W` directions in `maze.directions`; call `maze.solve()` to
recompute the route. `maze.regenerate()` changes the seed to a new unused value
and updates the grid, route, directions, and `generation_steps`. The
`ALGORITHMS` constant lists supported choices. `maze.to_hex_rows()` returns the
maze in the project's hexadecimal wall-flag format.

To build the wheel from the repository root, run:

```sh
uv build --wheel -o .
```

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
├── pyproject.toml                # Project and build configuration
├── uv.lock                       # Locked dependency versions
├── src/
│   ├── mazegen/                  # Reusable maze library
│   │   ├── dfs.py                # Depth-first generation engine
│   │   ├── maze_generator.py     # Public API and grid model
│   │   ├── pattern_42.py         # Reserved-cell pattern placement
│   │   ├── primm.py              # Prim generation engine
│   │   └── solver.py             # Breadth-first shortest-path search
│   ├── file_input.py             # Configuration parsing and validation
│   ├── file_output.py            # Maze and solution serialization
│   ├── maze_analyzer.py          # Output-file analysis utility
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

- The configuration parser requires `PERFECT`, validates that entry and exit
  are distinct and inside the grid, and supports optional `ALGORITHM` and
  `SEED` keys.
- A `42` pattern needs at least a 7-by-5 grid and can still be omitted if no
  placement preserves the required cells and connectivity.
- The application uses the packaged generator and BFS implementation through
  compatibility adapters.
- A graphical smoke test requires a Linux MiniLibX display. Headless unit tests
  can run without one.

## License

This project is distributed under the MIT License; see `LICENSE.md`.
