import sys
import time
from collections.abc import Callable
import ctypes
from itertools import pairwise
import os
from typing import Any, Protocol

from mlx import Mlx
from mazegen import ALGORITHMS, Grid, MazeGenerator, Point, Wall
from src.file_output import parse_output


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

    def mlx_string_put(
        self,
        mlx_ptr: Any,
        win_ptr: Any,
        x: int,
        y: int,
        color: int,
        string: str,
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
            if mlx is None:
                self._enable_fixed_window_size()

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
            self.display_grid = self._create_animation_grid(grid)

    def _enable_fixed_window_size(self) -> None:
        if os.name == "nt":
            return
        try:
            class MlxWin(ctypes.Structure):
                _fields_ = [
                    ("next", ctypes.c_void_p),
                    ("active", ctypes.c_int),
                    ("_padding", ctypes.c_int),
                    ("mlx", ctypes.c_void_p),
                    ("backend_win", ctypes.c_void_p),
                    ("gpu_win", ctypes.c_void_p),
                ]

            class XcbWin(ctypes.Structure):
                _fields_ = [
                    ("xcb", ctypes.c_void_p),
                    ("win_id", ctypes.c_uint),
                ]

            if self.win_ptr is None:
                return
            mlx_win = ctypes.cast(
                ctypes.c_void_p(int(self.win_ptr)),
                ctypes.POINTER(MlxWin),
            ).contents
            backend_win = ctypes.cast(
                mlx_win.backend_win,
                ctypes.POINTER(XcbWin),
            ).contents
            x_window = backend_win.win_id
            if not x_window:
                return

            x11 = ctypes.CDLL("libX11.so.6")
            x11.XOpenDisplay.restype = ctypes.c_void_p
            display = x11.XOpenDisplay(None)
            if not display:
                return

            x11.XInternAtom.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.c_int,
            ]
            x11.XInternAtom.restype = ctypes.c_ulong
            x11.XChangeProperty.argtypes = [
                ctypes.c_void_p,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_ulong),
                ctypes.c_int,
            ]

            allowed_property = x11.XInternAtom(
                display, b"_NET_WM_ALLOWED_ACTIONS", 0
            )
            atom_type = x11.XInternAtom(display, b"ATOM", 0)
            actions = (
                ctypes.c_ulong * 3
            )(
                x11.XInternAtom(display, b"_NET_WM_ACTION_CLOSE", 0),
                x11.XInternAtom(display, b"_NET_WM_ACTION_MINIMIZE", 0),
                x11.XInternAtom(display, b"_NET_WM_ACTION_MOVE", 0),
            )
            x11.XChangeProperty(
                display,
                x_window,
                allowed_property,
                atom_type,
                32,
                0,
                actions,
                3,
            )

            # Motif hints remove maximize/resize controls while keeping close,
            # minimize and move as normal window-manager functions.
            motif_property = x11.XInternAtom(
                display, b"_MOTIF_WM_HINTS", 0
            )
            motif_hints = (
                ctypes.c_ulong * 5
            )(
                2,
                1 << 2 | 1 << 3 | 1 << 5,
                0,
                0,
                0,
            )
            x11.XChangeProperty(
                display,
                x_window,
                motif_property,
                x11.XInternAtom(display, b"_MOTIF_WM_HINTS", 0),
                32,
                0,
                motif_hints,
                5,
            )

            normal_hints_property = x11.XInternAtom(
                display, b"WM_NORMAL_HINTS", 0
            )
            wm_size_hints = (
                ctypes.c_long * 18
            )(
                0 | 1 << 3 | 1 << 4 | 1 << 5,
                0,
                0,
                self.window_width,
                self.window_height,
                self.window_width,
                self.window_height,
                self.window_width,
                self.window_height,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            )
            x11.XChangeProperty.argtypes = [
                ctypes.c_void_p,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_long),
                ctypes.c_int,
            ]
            x11.XChangeProperty(
                display,
                x_window,
                normal_hints_property,
                x11.XInternAtom(display, b"WM_SIZE_HINTS", 0),
                32,
                0,
                wm_size_hints,
                18,
            )
            x11.XFlush(display)
            x11.XCloseDisplay(display)
        except (AttributeError, OSError, TypeError, ValueError):
            return

    def _draw_footer(self) -> None:
        self._fill_rectangle(
            0,
            self.control_y,
            self.window_width,
            self.window_height,
            0xFF160B1F,
        )

    def _draw_footer_text(self) -> None:
        algorithm_label = self.algorithm.upper()
        path_label = "ON" if self.show_path else "OFF"
        status = f"ALGORITHM  {algorithm_label}     PATH  {path_label}"
        legend_title = "KEY LEGEND"
        legend_top = "[1] DFS  [2] Prim  [P] Path"
        legend_bottom = "[C] Colour  [R] New  [Q] Exit"

        self.mlx.mlx_string_put(
            self.mlx_ptr,
            self.win_ptr,
            self.margin,
            self.control_y + 24,
            0xFFE879F9,
            status,
        )
        self.mlx.mlx_string_put(
            self.mlx_ptr,
            self.win_ptr,
            self.margin,
            self.control_y + 46,
            0xFFF43F5E,
            legend_title,
        )
        top_x = max(
            self.margin,
            (self.window_width - len(legend_top) * 7) // 2,
        )
        self.mlx.mlx_string_put(
            self.mlx_ptr,
            self.win_ptr,
            top_x,
            self.control_y + 68,
            0xFFE6EDF3,
            legend_top,
        )
        bottom_x = max(
            self.margin,
            (self.window_width - len(legend_bottom) * 7) // 2,
        )
        self.mlx.mlx_string_put(
            self.mlx_ptr,
            self.win_ptr,
            bottom_x,
            self.control_y + 92,
            0xFFE6EDF3,
            legend_bottom,
        )

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
        self._buffer_ready = True
        self._present_image()

    def _present_image(self) -> None:
        """Display the current image and overlay the keyboard controls."""
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.image, 0, 0
        )
        self._draw_footer_text()

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
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def handle_expose(self, _param: Any = None) -> None:
        if self._buffer_ready:
            self._present_image()
        else:
            self.draw_maze()

    def _cleanup(self, suppress_errors: bool = False) -> None:
        first_error = None
        if self.image is not None:
            try:
                self.mlx.mlx_destroy_image(self.mlx_ptr, self.image)
            except Exception as error:
                if first_error is None:
                    first_error = error
            finally:
                self.image = None
                self.data = memoryview(b"")
        if self.win_ptr is not None:
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
        try:
            self.draw_maze()
            self.mlx.mlx_key_hook(self.win_ptr, self.handle_key, None)
            self.mlx.mlx_expose_hook(self.win_ptr, self.handle_expose, None)
            self.mlx.mlx_loop_hook(
                self.mlx_ptr, self.animation_tick, None
            )
            self.mlx.mlx_hook(
                self.win_ptr, 33, 0, self.close_window, None
            )
            self.mlx.mlx_loop(self.mlx_ptr)
        finally:
            self._cleanup()
