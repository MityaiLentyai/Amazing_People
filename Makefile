.PHONY: install run debug clean lint lint-strict

PYTHON ?= python3

install:
	uv sync

run:
	$(PYTHON) a_maze_ing.py config.txt

debug:
	$(PYTHON) -m pdb a_maze_ing.py config.txt

clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p) if p.is_dir() else p.unlink() for p in pathlib.Path('.').rglob('__pycache__')]; cache=pathlib.Path('.mypy_cache'); shutil.rmtree(cache, ignore_errors=True)"

lint:
	uv run flake8 src a_maze_ing.py tests
	uv run mypy a_maze_ing.py src/file_input.py src/file_output.py src/visualizer.py --explicit-package-bases --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 src a_maze_ing.py tests
	uv run mypy a_maze_ing.py src/file_input.py src/file_output.py src/visualizer.py --explicit-package-bases --strict --ignore-missing-imports
