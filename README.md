# Amazing_People
Doing amazing things

## Setup with uv
Install [uv](https://docs.astral.sh/uv/) if needed, then from the project root run `uv sync` to create `.venv` and install dependencies from `uv.lock` (Python 3.14 is pinned via `.python-version`). 

Useful commands:
* `uv sync` (recreate / refresh the env)
* `uv run a-maze-ing config.txt` 

## Using the wheel

Using Python 3.10+, run from the repository root. The test runs outside the repository to check the installed package:

```sh
python3 -m venv /tmp/mazegen-eval
. /tmp/mazegen-eval/bin/activate
python3 -m pip install --force-reinstall ./mazegen-0.1.0-py3-none-any.whl
cd /tmp
python3 - <<'PY'
from src.file_input import Config
from src.maze_generator import generate_maze
from src.bfs import BFS

config = Config(WIDTH=20, HEIGHT=15, ENTRY=(0, 0), EXIT=(19, 14),
                OUTPUT_FILE="unused.txt", PERFECT=True, SEED=43)
maze = generate_maze(config)
path = BFS(maze).find_path()
assert path and path[0] == maze.start and path[-1] == maze.end
assert all(maze.is_open_passage(a, b) for a, b in zip(path, path[1:]))
assert len(maze.reserved_cells) == 20
assert all(maze.cells[p.y][p.x] == 15 for p in maze.reserved_cells)
print("OK: maze, solution and 42 glyph")
PY
```

Expected output: `OK: maze, solution and 42 glyph`.

## File structure
```text
.
├── LICENSE
├── README.md
├── a_maze_ing.py        ----- SUBJECT ENTRY: python3 a_maze_ing.py config.txt
├── amazeing.pdf
├── config.txt
├── output.txt
├── pyproject.toml       ----- HERE WE STORE STUFF FOR uv + virtual env
├── src                  ----- HERE WE HAVE ALGORITHMS + VISUALISATION
│   └── ├── __init__.py
│       ├── cli.py
│       ├── file_input.py
│       └── file_output.py
└── uv.lock              ----- DON'T DELETE THIS NEEDED FOR EVAL

2 directories, 10 files
```
