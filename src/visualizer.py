import sys
import time
from collections.abc import Callable
from typing import Any, Protocol

from mlx import Mlx
from src.maze_generator import Grid, Point, Wall


class MlxApi(Protocol):
    def mlx_init(self) -> Any: ...

    def mlx_new_window(self, mlx_ptr, width, height, title, /) -> Any: ...

    def mlx_new_image(self, mlx_ptr, width, height, /) -> Any: ...

    def mlx_get_data_addr(
        self, image, /
    ) -> tuple[memoryview, int, int, int]: ...

    def mlx_put_image_to_window(
        self, mlx_ptr, win_ptr, image, x, y, /
    ) -> Any: ...

    def mlx_string_put(
        self, mlx_ptr, win_ptr, x, y, color, string, /
    ) -> Any: ...

    def mlx_key_hook(self, win_ptr, callback, param, /) -> Any: ...

    def mlx_mouse_hook(self, win_ptr, callback, param, /) -> Any: ...

    def mlx_expose_hook(self, win_ptr, callback, param, /) -> Any: ...

    def mlx_hook(self, win_ptr, event, mask, callback, param, /) -> Any: ...

    def mlx_loop(self, mlx_ptr, /) -> Any: ...

    def mlx_loop_hook(self, mlx_ptr, callback, param, /) -> Any: ...

    def mlx_loop_exit(self, mlx_ptr, /) -> Any: ...

    def mlx_destroy_image(self, mlx_ptr, image, /) -> Any: ...

    def mlx_destroy_window(self, mlx_ptr, win_ptr, /) -> Any: ...

    def mlx_release(self, mlx_ptr, /) -> Any: ...


class MazeRenderer:
    background_color = 0xFF141922
    reserved_color = 0xFF344054
    path_color = 0xFFFFC857
    start_color = 0xFF2ECC71
    end_color = 0xFFE74C3C
    wall_colors = (0xFFE6EDF3, 0xFF7BDFF2, 0xFFFFAFCC, 0xFFC1FBA4)

    def __init__(
        self,
        grid: Grid,
        path: list[Point] | None = None,
        regenerate: Callable[
            [], tuple[Grid, list[Point], list[tuple[Point, Point]]]
        ] | None = None,
        *,
        generation_steps: list[tuple[Point, Point]] | None = None,
        mlx: MlxApi | None = None,
    ):
        self.grid = grid
        self.path = path or []
        self.regenerate = regenerate
        self.show_path = True
        self.wall_color_index = 0
        self.cell_size = 50
        self.margin = 20
        self.controls_gap = 14
        self.button_height = 36
        self.control_y = self.margin + grid.height * self.cell_size + self.controls_gap
        self.button_gap = 8
        self.window_width = max(
            grid.width * self.cell_size + 2 * self.margin, 280
        )
        self.window_height = self.control_y + self.button_height + self.margin
        self._set_generation(grid, self.path, generation_steps)

        self.mlx = mlx if mlx is not None else Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.win_ptr = None
        self.image = None
        self.data: memoryview = memoryview(b"")

        if not self.mlx_ptr:
            raise RuntimeError("MiniLibX could not connect to a display")

        try:
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

            self.data, self.bpp, self.size_line, self.endian = \
                self.mlx.mlx_get_data_addr(self.image)
            if self.bpp != 32 or self.endian not in (0, 1):
                raise RuntimeError(
                    f"Unsupported MiniLibX image format: "
                    f"{self.bpp} bpp, format {self.endian}"
                )
            if self.size_line < self.window_width * 4:
                raise RuntimeError("MiniLibX image row is shorter than its width")
            if len(self.data) < self.size_line * self.window_height:
                raise RuntimeError("MiniLibX returned an incomplete image buffer")
        except Exception:
            self._cleanup(suppress_errors=True)
            raise

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
        self.steps_per_frame = max(1, len(self.generation_steps) // 180)
        self.last_animation_time = 0.0
        if generation_steps is None or not self.generation_steps:
            self.display_grid = grid
            self.animation_index = len(self.generation_steps)
        else:
            self.display_grid = self._create_animation_grid(grid)

    def _button_bounds(self) -> tuple[tuple[int, int, int, int], ...]:
        left = self.margin
        available_width = self.window_width - 2 * self.margin - self.button_gap
        button_width = available_width // 2
        return (
            (
                left,
                self.control_y,
                left + button_width,
                self.control_y + self.button_height,
            ),
            (
                left + button_width + self.button_gap,
                self.control_y,
                self.window_width - self.margin,
                self.control_y + self.button_height,
            ),
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

    def _draw_line(self, x0: int, y0: int, x1: int, y1: int,
                   color: int, thickness: int = 5) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        radius = thickness // 2

        while True:
            self._fill_rectangle(
                x0 - radius,
                y0 - radius,
                x0 + radius + 1,
                y0 + radius + 1,
                color,
            )
            if x0 == x1 and y0 == y1:
                break
            twice_error = 2 * error
            if twice_error >= dy:
                error += dy
                x0 += sx
            if twice_error <= dx:
                error += dx
                y0 += sy

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

        centers = [
            (
                self.margin + point.x * self.cell_size + self.cell_size // 2,
                self.margin + point.y * self.cell_size + self.cell_size // 2,
            )
            for point in self.path
        ]
        for (x0, y0), (x1, y1) in zip(centers, centers[1:]):
            self._draw_line(x0, y0, x1, y1, self.path_color)

    def _draw_marker(self, point: Point, color: int) -> None:
        center_x = self.margin + point.x * self.cell_size + self.cell_size // 2
        center_y = self.margin + point.y * self.cell_size + self.cell_size // 2
        radius = max(3, self.cell_size // 4)
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
        self._fill_background()

        for point in self.display_grid.reserved_cells:
            x0 = self.margin + point.x * self.cell_size + 2
            y0 = self.margin + point.y * self.cell_size + 2
            self._fill_rectangle(
                x0,
                y0,
                x0 + self.cell_size - 4,
                y0 + self.cell_size - 4,
                self.reserved_color,
            )

        self._draw_path()

        for y in range(self.display_grid.height):
            for x in range(self.display_grid.width):
                cell = self.display_grid.cells[y][x]

                x0 = self.margin + x * self.cell_size
                y0 = self.margin + y * self.cell_size

                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size

                if cell & Wall.NORTH:
                    self.draw_horizontal(x0, x1, y0, self.wall_color)

                if cell & Wall.EAST:
                    self.draw_vertical(x1, y0, y1, self.wall_color)

                if cell & Wall.SOUTH:
                    self.draw_horizontal(x0, x1, y1, self.wall_color)

                if cell & Wall.WEST:
                    self.draw_vertical(x0, y0, y1, self.wall_color)

        self._draw_marker(self.display_grid.start, self.start_color)
        self._draw_marker(self.display_grid.end, self.end_color)
        first_button, second_button = self._button_bounds()
        self._fill_rectangle(*first_button, 0xFF344054)
        self._fill_rectangle(*second_button, 0xFF344054)
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.image, 0, 0
        )
        labels = ("New maze", "Hide path" if self.show_path else "Show path")
        for bounds, label in zip((first_button, second_button), labels):
            x0, y0, x1, _y1 = bounds
            text_x = x0 + max(4, (x1 - x0 - len(label) * 8) // 2)
            self.mlx.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                text_x,
                y0 + 23,
                0xFFFFFFFF,
                label,
            )

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

    def handle_mouse(
        self, button: int, x: int, y: int, _param=None
    ) -> None:
        if button != 1:
            return
        first_button, second_button = self._button_bounds()
        if self._contains(first_button, x, y):
            self.generate_new_maze()
        elif self._contains(second_button, x, y):
            self.toggle_path()

    @staticmethod
    def _contains(bounds: tuple[int, int, int, int], x: int, y: int) -> bool:
        x0, y0, x1, y1 = bounds
        return x0 <= x < x1 and y0 <= y < y1

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
            self.display_grid.open_passage(point1, point2)
        self.animation_index = stop
        if self.animation_complete:
            self.display_grid = self.grid
        self.draw_maze()
        return True

    def animation_tick(self, _param=None) -> int:
        self.advance_animation()
        return 0

    def handle_key(self, key: int | str, _param=None) -> None:
        if isinstance(key, str):
            key_name = key.lower()
        elif key in (27, 65307):
            key_name = "escape"
        else:
            try:
                key_name = chr(key).lower()
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

    def close_window(self, _param=None) -> None:
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def handle_expose(self, _param=None) -> None:
        self.draw_maze()

    def _cleanup(self, suppress_errors: bool = False) -> None:
        first_error = None
        resources = (
            ("image", self.image, self.mlx.mlx_destroy_image),
            ("window", self.win_ptr, self.mlx.mlx_destroy_window),
            ("mlx", self.mlx_ptr, self.mlx.mlx_release),
        )
        for name, resource, destroy in resources:
            if resource is None:
                continue
            try:
                if name == "mlx":
                    destroy(resource)
                else:
                    destroy(self.mlx_ptr, resource)
            except Exception as error:
                if first_error is None:
                    first_error = error
            finally:
                if name == "image":
                    self.image = None
                    self.data = memoryview(b"")
                elif name == "window":
                    self.win_ptr = None
                else:
                    self.mlx_ptr = None

        if first_error is not None and not suppress_errors:
            raise first_error

    def run(self) -> None:
        try:
            self.draw_maze()
            self.mlx.mlx_key_hook(self.win_ptr, self.handle_key, None)
            self.mlx.mlx_mouse_hook(self.win_ptr, self.handle_mouse, None)
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
