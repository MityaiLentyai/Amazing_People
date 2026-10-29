# Amazing_People
Doing amazing things

## Setup with uv
Install [uv](https://docs.astral.sh/uv/) if needed, then from the project root run `uv sync` to create `.venv` and install dependencies from `uv.lock` (Python 3.14 is pinned via `.python-version`). 

Useful evaluation commands:
* `uv sync` (recreate / refresh the env)
* `uv run python a_maze_ing.py config.txt` (subject-style entry; also works as `python3 a_maze_ing.py config.txt` after `source .venv/bin/activate`)
* `uv run a-maze-ing config.txt` (same app via the installed script)
* `uv run a-maze-ing` / `python3 a_maze_ing.py` (prints usage and exits)

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
