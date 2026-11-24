import sys
import time
import weakref
from collections.abc import Callable
from itertools import pairwise
from typing import Any, Protocol

from mlx import Mlx
from mazegen import ALGORITHMS, Grid, MazeGenerator, Point, Wall
from src.file_output import parse_output


# Each glyph stores seven rows of five bits, most significant bit first.
FOOTER_GLYPHS = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "W": (17, 17, 17, 21, 21, 27, 17),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31),
    "[": (14, 8, 8, 8, 8, 8, 14),
    "]": (14, 2, 2, 2, 2, 2, 14),
}


class MlxApi(Protocol):
    def mlx_init(self) -> Any: ...

    def mlx_new_window(
        self, mlx_ptr: Any, width: int, height: int, title: str, /
    ) -> Any: ...

    def mlx_new_image(
        self, mlx_ptr: Any, width: int, height: int, /
    ) -> Any: ...

    def mlx_get_data_addr(
        self, image: Any, /
    ) -> tuple[memoryview, int, int, int]: ...

    def mlx_put_image_to_window(
        self,
        mlx_ptr: Any,
        win_ptr: Any,
        image: Any,
        x: int,
        y: int,
        /,
    ) -> Any: ...

    def mlx_key_hook(
        self,
        win_ptr: Any,
        callback: Callable[..., Any] | None,
        param: Any,
        /,
    ) -> Any: ...

    def mlx_mouse_hook(
        self,
        win_ptr: Any,
        callback: Callable[..., Any] | None,
        param: Any,
        /,
    ) -> Any: ...

    def mlx_expose_hook(
        self,
        win_ptr: Any,
        callback: Callable[..., Any] | None,
        param: Any,
        /,
    ) -> Any: ...

    def mlx_hook(
        self,
        win_ptr: Any,
        event: int,
        mask: int,
        callback: Callable[..., Any] | None,
        param: Any,
        /,
    ) -> Any: ...

    def mlx_loop(self, mlx_ptr: Any, /) -> Any: ...

    def mlx_loop_hook(
        self,
        mlx_ptr: Any,
        callback: Callable[..., Any] | None,
        param: Any,
        /,
    ) -> Any: ...

    def mlx_loop_exit(self, mlx_ptr: Any, /) -> Any: ...

    def mlx_destroy_image(
        self, mlx_ptr: Any, image: Any, /
    ) -> Any: ...

    def mlx_destroy_window(
        self, mlx_ptr: Any, win_ptr: Any, /
    ) -> Any: ...

    def mlx_release(self, mlx_ptr: Any, /) -> Any: ...


class MazeRenderer:
    """Animate maze generation and draw the result in a MiniLibX window."""

    background_color = 0xFF09090B
    reserved_color = 0xFF3A1C52
    path_color = 0xFFE879F9
    start_color = 0xFFA78BFA
    end_color = 0xFFF43F5E
    wall_colors = (0xFF9D174D, 0xFFA855F7, 0xFF7C3AED, 0xFFE11D48)

    @classmethod
    def from_generator(
        cls,
        maze: MazeGenerator,
        output_file: str | None = None,
        *,
        mlx: MlxApi | None = None,
    ) -> "MazeRenderer":
        return cls(
            maze.grid,
            maze.path,
            cls._make_regenerator(maze, output_file),
            generation_steps=maze.generation_steps,
            algorithm=maze.algorithm,
            algorithm_switch=cls._make_algorithm_switcher(
                maze, output_file
            ),
            mlx=mlx,
        )

    @staticmethod
    def _make_algorithm_switcher(
        maze: MazeGenerator,
        output_file: str | None,
    ) -> Callable[[str], tuple[Grid, list[Point], list[tuple[Point, Point]]]]:
        def switch_algorithm(
            algorithm: str,
        ) -> tuple[Grid, list[Point], list[tuple[Point, Point]]]:
            normalized = algorithm.lower()
            if normalized not in ALGORITHMS:
                raise ValueError(
                    f"Algorithm must be one of: {', '.join(ALGORITHMS)}"
                )
            maze.algorithm = normalized
            grid = maze.regenerate()
            path = maze.path
            if path is None:
                raise RuntimeError(
                    "Switched-algorithm maze has no path from entry to exit"
                )
            if output_file is not None:
                parse_output(output_file, maze.directions, grid)
            return grid, path, maze.generation_steps

        return switch_algorithm

    @staticmethod
    def _make_regenerator(
        maze: MazeGenerator,
        output_file: str | None,
    ) -> Callable[[], tuple[Grid, list[Point], list[tuple[Point, Point]]]]:
        def regenerate() -> tuple[Grid, list[Point],
                                  list[tuple[Point, Point]]]:
            grid = maze.regenerate()
            path = maze.path
            if path is None:
                raise RuntimeError(
                    "Regenerated maze has no path from entry to exit")

            if output_file is not None:
                parse_output(output_file, maze.directions, grid)
            return grid, path, maze.generation_steps

        return regenerate

    def __init__(
        self,
        grid: Grid,
        path: list[Point] | None = None,
        regenerate: Callable[
            [], tuple[Grid, list[Point], list[tuple[Point, Point]]]
        ] | None = None,
        *,
        generation_steps: list[tuple[Point, Point]] | None = None,
        algorithm: str = "dfs",
        algorithm_switch: Callable[
            [str], tuple[Grid, list[Point], list[tuple[Point, Point]]]
        ] | None = None,
        mlx: MlxApi | None = None,
    ):
        self.grid = grid
        self.path = path or []
        self.regenerate = regenerate
        self.algorithm = algorithm.lower()
        self.algorithm_switch = algorithm_switch
        self.show_path = True
        self.wall_color_index = 0
        self.margin = 20
        self.controls_gap = 12
        self.footer_height = 112
        self._set_generation(grid, self.path, generation_steps)

        self.mlx = mlx if mlx is not None else Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.win_ptr = None
        self.image = None
        self.data: memoryview = memoryview(b"")
        self.bpp = 0
        self.size_line = 0
        self.endian = 0

        if not self.mlx_ptr:
            raise RuntimeError("MiniLibX could not connect to a display")

        try:
            self._fit_window(grid)
            self.win_ptr = self.mlx.mlx_new_window(
                self.mlx_ptr,
                self.window_width,
                self.window_height,
                "A-Maze-ing",
            )
            if not self.win_ptr:
                raise RuntimeError("MiniLibX could not create a window")

            self.image = self.mlx.mlx_new_image(
                self.mlx_ptr,
                self.window_width,
                self.window_height,
            )
            if not self.image:
                raise RuntimeError("MiniLibX could not create an image")

            (
                self.data,
                self.bpp,
                self.size_line,
                self.endian,
            ) = self.mlx.mlx_get_data_addr(self.image)
            # The view borrows native image memory. MLX supplies the
            # row stride, which can include padding after the last pixel.
            if self.bpp != 32 or self.endian not in (0, 1):
                raise RuntimeError(
                    f"Unsupported MiniLibX image format: "
                    f"{self.bpp} bpp, format {self.endian}"
                )
            if self.size_line < self.window_width * 4:
                raise RuntimeError(
                    "MiniLibX image row is shorter than its width")
            if len(self.data) < self.size_line * self.window_height:
                raise RuntimeError(
                    "MiniLibX returned an incomplete image buffer")
        except Exception:
            self._cleanup(suppress_errors=True)
            raise

    def _fit_window(self, grid: Grid) -> None:
        """Fit the maze and controls in the available screen space."""
        screen_width, screen_height = 1280, 800
        get_screen_size = getattr(self.mlx, "mlx_get_screen_size", None)
        if get_screen_size is not None:
            try:
                _, width, height = get_screen_size(self.mlx_ptr)
                if width > 0 and height > 0:
                    screen_width, screen_height = width, height
            except (AttributeError, OSError):
                pass

        max_width = screen_width - 32
        max_height = screen_height - 80
        footer_space = self.margin + self.controls_gap + self.footer_height
        self.cell_size = min(
            50,
            (max_width - 2 * self.margin - 1) // grid.width,
            (max_height - footer_space) // grid.height,
        )
        if self.cell_size < 4 or max_width < 280:
            raise RuntimeError("Maze is too large to display on this screen")

        self.control_y = (
            self.margin + grid.height * self.cell_size + self.controls_gap
        )
        self.window_width = max(
            grid.width * self.cell_size + 2 * self.margin + 1, 280
        )
        self.window_height = self.control_y + self.footer_height

    @property
    def wall_color(self) -> int:
        return self.wall_colors[self.wall_color_index]

    @property
    def animation_complete(self) -> bool:
        return self.animation_index >= len(self.generation_steps)

    def _create_animation_grid(self, grid: Grid) -> Grid:
        visible_grid = Grid(
            grid.width, grid.height, grid.start, grid.end, grid.perfect
        )
        visible_grid.reserve_cells(grid.reserved_cells)
        return visible_grid

    def _set_generation(
        self,
        grid: Grid,
        path: list[Point],
        generation_steps: list[tuple[Point, Point]] | None,
    ) -> None:
        self.grid = grid
        self.path = path
        self.generation_steps = list(generation_steps or [])
        self.animation_index = 0
        self._buffer_ready = False
        self.steps_per_frame = max(1, len(self.generation_steps) // 180)
        self.last_animation_time = 0.0
        if generation_steps is None or not self.generation_steps:
            self.display_grid = grid
            self.animation_index = len(self.generation_steps)
        else:
            # Replay passages on a separate grid so the solved maze stays
            # intact while the animation is still showing closed walls.
            self.display_grid = self._create_animation_grid(grid)

    def _draw_footer(self) -> None:
        self._fill_rectangle(
            0,
            self.control_y,
            self.window_width,
            self.window_height,
            0xFF160B1F,
        )

    def _draw_footer_text(self) -> None:
        path_label = "ON" if self.show_path else "OFF"
        self._draw_text(
            f"ALGORITHM  {self.algorithm.upper()}     PATH  {path_label}",
            self.control_y + 14,
            0xFFE879F9,
        )
        self._draw_text("KEY LEGEND", self.control_y + 37, 0xFFF43F5E)
        self._draw_text("[1] DFS  [2] PRIM  [P] PATH", self.control_y + 60)
        self._draw_text("[C] COLOUR  [R] NEW  [Q] EXIT", self.control_y + 84)

    def _draw_text(self, text: str, y: int, color: int = 0xFFE6EDF3) -> None:
        # MLX 2.2 leaves a stale native font pointer after mlx_release.
        # Paint the footer into the same buffer as the maze.
        advance = 9
        x = (self.window_width - len(text) * advance) // 2
        for char in text:
            for row, bits in enumerate(FOOTER_GLYPHS.get(char, ())):
                for col in range(5):
                    if bits & (16 >> col):
                        top = y + row * 2
                        self._fill_rectangle(
                            x + col, top, x + col + 1, top + 2, color
                        )
            x += advance

    def _pixel_bytes(self, color: int) -> bytes:
        alpha = (color >> 24) & 0xFF
        red = (color >> 16) & 0xFF
        green = (color >> 8) & 0xFF
        blue = color & 0xFF
        if self.endian == 0:
            return bytes((blue, green, red, alpha))
        return bytes((alpha, red, green, blue))

    def _fill_rectangle(
        self, x0: int, y0: int, x1: int, y1: int, color: int
    ) -> None:
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.window_width, x1)
        y1 = min(self.window_height, y1)
        if x0 >= x1 or y0 >= y1:
            return

        pixel = self._pixel_bytes(color)
        row = pixel * (x1 - x0)
        for y in range(y0, y1):
            offset = y * self.size_line + x0 * 4
            self.data[offset:offset + len(row)] = row

    def _fill_background(self) -> None:
        pixel = self._pixel_bytes(self.background_color)
        row = pixel * self.window_width
        for y in range(self.window_height):
            offset = y * self.size_line
            self.data[offset:offset + len(row)] = row

    def _draw_path(self) -> None:
        if (
            not self.show_path
            or not self.path
            or not self.animation_complete
        ):
            return

        centers = (
            (
                self.margin + point.x * self.cell_size + self.cell_size // 2,
                self.margin + point.y * self.cell_size + self.cell_size // 2,
            )
            for point in self.path
        )
        radius = min(2, (self.cell_size - 2) // 2)
        for (x0, y0), (x1, y1) in pairwise(centers):
            self._fill_rectangle(
                min(x0, x1) - radius,
                min(y0, y1) - radius,
                max(x0, x1) + radius + 1,
                max(y0, y1) + radius + 1,
                self.path_color,
            )

    def _draw_marker(self, point: Point, color: int) -> None:
        center_x = self.margin + point.x * self.cell_size + self.cell_size // 2
        center_y = self.margin + point.y * self.cell_size + self.cell_size // 2
        radius = max(1, self.cell_size // 4)
        for dy in range(-radius, radius + 1):
            half_width = int((radius * radius - dy * dy) ** 0.5)
            self._fill_rectangle(
                center_x - half_width,
                center_y + dy,
                center_x + half_width + 1,
                center_y + dy + 1,
                color,
            )

    def draw_horizontal(self, x1: int, x2: int, y: int,
                        color: int) -> None:
        self._fill_rectangle(x1, y, x2 + 1, y + 1, color)

    def draw_vertical(self, x: int, y1: int, y2: int,
                      color: int) -> None:
        self._fill_rectangle(x, y1, x + 1, y2 + 1, color)

    def draw_maze(self) -> None:
        """Rebuild the image after a change affecting the whole maze."""
        self._fill_background()

        inset = 1 if self.cell_size < 8 else 2
        for point in self.display_grid.reserved_cells:
            x0 = self.margin + point.x * self.cell_size
            y0 = self.margin + point.y * self.cell_size
            self._fill_rectangle(
                x0 + inset,
                y0 + inset,
                x0 + self.cell_size - inset + 1,
                y0 + self.cell_size - inset + 1,
                self.reserved_color,
            )

        self._draw_path()

        color = self.wall_color
        for y, row in enumerate(self.display_grid.cells):
            for x, cell in enumerate(row):
                x0 = self.margin + x * self.cell_size
                y0 = self.margin + y * self.cell_size

                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size

                if cell & Wall.NORTH:
                    self.draw_horizontal(x0, x1, y0, color)

                if x == self.display_grid.width - 1 and cell & Wall.EAST:
                    self.draw_vertical(x1, y0, y1, color)

                if y == self.display_grid.height - 1 and cell & Wall.SOUTH:
                    self.draw_horizontal(x0, x1, y1, color)

                if cell & Wall.WEST:
                    self.draw_vertical(x0, y0, y1, color)

        self._draw_marker(self.display_grid.start, self.start_color)
        self._draw_marker(self.display_grid.end, self.end_color)
        self._draw_footer()
        self._draw_footer_text()
        self._buffer_ready = True
        self._present_image()

    def _present_image(self) -> None:
        """Blit the completed framebuffer to the window."""
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.image, 0, 0
        )

    def _erase_open_wall(self, first: Point, second: Point) -> None:
        """Erase an opened wall and remove any newly empty junctions."""
        x, y = max(first.x, second.x), max(first.y, second.y)
        left = self.margin + x * self.cell_size
        top = self.margin + y * self.cell_size
        if first.x == second.x:
            self.draw_horizontal(
                left + 1, left + self.cell_size - 1, top,
                self.background_color,
            )
            self._erase_empty_junction(x + 1, y)
        else:
            self.draw_vertical(
                left, top + 1, top + self.cell_size - 1,
                self.background_color,
            )
            self._erase_empty_junction(x, y + 1)
        self._erase_empty_junction(x, y)

    def _erase_empty_junction(self, x: int, y: int) -> None:
        """Clear a wall endpoint only if none of its incident walls remain."""
        grid = self.display_grid
        if x in (0, grid.width) or y in (0, grid.height):
            return  # The maze's outer wall always touches this junction.
        cell = grid.cells[y][x]
        if (
            cell & (Wall.NORTH | Wall.WEST)
            or grid.cells[y - 1][x] & Wall.WEST
            or grid.cells[y][x - 1] & Wall.NORTH
        ):
            return
        left = self.margin + x * self.cell_size
        top = self.margin + y * self.cell_size
        self._fill_rectangle(left, top, left + 1, top + 1,
                             self.background_color)

    def toggle_path(self) -> None:
        self.show_path = not self.show_path
        self.draw_maze()

    def generate_new_maze(self) -> None:
        if self.regenerate is None:
            return
        try:
            grid, path, generation_steps = self.regenerate()
            self._set_generation(grid, path, generation_steps)
            self.draw_maze()
        except Exception as error:
            print(f"Could not regenerate maze: {error}", file=sys.stderr)

    def select_algorithm(self, algorithm: str) -> None:
        if self.algorithm_switch is None:
            return
        normalized = algorithm.lower()
        if normalized not in ALGORITHMS:
            return
        try:
            grid, path, generation_steps = self.algorithm_switch(normalized)
            self.algorithm = normalized
            self._set_generation(grid, path, generation_steps)
            self.draw_maze()
        except Exception as error:
            print(
                f"Could not switch to {normalized.upper()}: {error}",
                file=sys.stderr,
            )

    def handle_mouse(
        self,
        _button: int,
        _x: int,
        _y: int,
        _param: Any = None,
    ) -> None:
        return

    def advance_animation(self, force: bool = False) -> bool:
        if self.animation_complete:
            return False
        now = time.monotonic()
        if not force and now - self.last_animation_time < 0.025:
            return False
        self.last_animation_time = now
        stop = min(
            self.animation_index + self.steps_per_frame,
            len(self.generation_steps),
        )
        for point1, point2 in self.generation_steps[self.animation_index:stop]:
            if (
                self.display_grid.open_passage(point1, point2)
                and self._buffer_ready
            ):
                self._erase_open_wall(point1, point2)
        self.animation_index = stop
        if self.animation_complete:
            self.display_grid = self.grid
            self.draw_maze()
        elif self._buffer_ready:
            self._present_image()
        else:
            self.draw_maze()
        return True

    def animation_tick(self, _param: Any = None) -> int:
        if self.animation_complete:
            time.sleep(0.01)
        else:
            self.advance_animation()
        return 0

    def handle_key(
        self,
        key: int | str,
        _param: Any = None,
    ) -> None:
        if isinstance(key, str):
            key_name = key.lower()
        elif key in (27, 65307):
            key_name = "escape"
        else:
            try:
                normalized_key = key
                if 65 <= normalized_key <= 90:
                    normalized_key += 32
                key_name = chr(normalized_key).lower()
            except (TypeError, ValueError):
                return

        if key_name in ("escape", "q"):
            self.close_window(None)
        elif key_name == "p":
            self.toggle_path()
        elif key_name == "c":
            self.wall_color_index = (
                self.wall_color_index + 1
            ) % len(self.wall_colors)
            self.draw_maze()
        elif key_name == "r" and self.regenerate is not None:
            self.generate_new_maze()
        elif key_name in ("1", "d"):
            self.select_algorithm("dfs")
        elif key_name == "2":
            self.select_algorithm("prim")
        elif key_name == "a":
            next_algorithm = (
                "prim" if self.algorithm == "dfs" else "dfs"
            )
            self.select_algorithm(next_algorithm)

    def close_window(self, _param: Any = None) -> None:
        # Let MLX finish dispatching this event before freeing its resources.
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def handle_expose(self, _param: Any = None) -> None:
        if self._buffer_ready:
            self._present_image()
        else:
            self.draw_maze()

    def _cleanup(self, suppress_errors: bool = False) -> None:
        first_error = None
        if self.image:
            try:
                self.data.release()
                self.mlx.mlx_destroy_image(self.mlx_ptr, self.image)
            except Exception as error:
                if first_error is None:
                    first_error = error
            finally:
                self.image = None
                self.data = memoryview(b"")
        if self.win_ptr:
            try:
                self.mlx.mlx_destroy_window(
                    self.mlx_ptr,
                    self.win_ptr,
                )
            except Exception as error:
                if first_error is None:
                    first_error = error
            finally:
                self.win_ptr = None
        if self.mlx_ptr is not None:
            try:
                self.mlx.mlx_release(self.mlx_ptr)
            except Exception as error:
                if first_error is None:
                    first_error = error
            finally:
                self.mlx_ptr = None

        if first_error is not None and not suppress_errors:
            raise first_error

    def run(self) -> None:
        # MLX keeps callback objects after teardown. Capture a weak proxy
        # so a reused MLX wrapper cannot retain this renderer and its grids.
        renderer = weakref.proxy(self)
        try:
            self.draw_maze()
            self.mlx.mlx_key_hook(
                self.win_ptr, lambda key, param: renderer.handle_key(
                    key, param
                ), None
            )
            self.mlx.mlx_expose_hook(
                self.win_ptr, lambda param: renderer.handle_expose(param),
                None
            )
            self.mlx.mlx_loop_hook(
                self.mlx_ptr, lambda param: renderer.animation_tick(param),
                None
            )
            self.mlx.mlx_hook(
                self.win_ptr, 33, 0,
                lambda param: renderer.close_window(param), None
            )
            self.mlx.mlx_loop(self.mlx_ptr)
        finally:
            self._cleanup()
