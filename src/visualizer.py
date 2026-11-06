
from mlx import Mlx

from src.maze_generator import Grid, Wall


class MazeRenderer:
    def __init__(self, grid: Grid):
        self.grid = grid
        self.mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()

        self.cell_size = 30
        self.margin = 20

        self.window_width = grid.width * self.cell_size + 2 * self.margin
        self.window_height = grid.height * self.cell_size + 2 * self.margin

        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr,
            self.window_width,
            self.window_height,
            "A-Maze-ing"
        )

    def draw_horizontal(self, x1: int, x2: int, y: int,
                        color: int) -> None:
        for x in range(x1, x2 + 1):
            self.mlx.mlx_pixel_put(
                self.mlx_ptr, self.win_ptr, x, y, color
            )

    def draw_vertical(self, x: int, y1: int, y2: int,
                      color: int) -> None:
        for y in range(y1, y2 + 1):
            self.mlx.mlx_pixel_put(
                self.mlx_ptr, self.win_ptr, x, y, color
            )

    def draw_maze(self) -> None:
        white = 0xFFFFFF

        for y in range(self.grid.height):
            for x in range(self.grid.width):
                cell = self.grid.cells[y][x]

                x0 = self.margin + x * self.cell_size
                y0 = self.margin + y * self.cell_size

                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size

                if cell & Wall.NORTH:
                    self.draw_horizontal(x0, x1, y0, white)

                if cell & Wall.EAST:
                    self.draw_vertical(x1, y0, y1, white)

                if cell & Wall.SOUTH:
                    self.draw_horizontal(x0, x1, y1, white)

                if cell & Wall.WEST:
                    self.draw_vertical(x0, y0, y1, white)

    def close_window(self, _param) -> None:
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def run(self) -> None:
        self.draw_maze()

        self.mlx.mlx_hook(
            self.win_ptr, 33, 0, self.close_window, None
        )

        self.mlx.mlx_loop(self.mlx_ptr)

        self.mlx.mlx_destroy_window(self.mlx_ptr, self.win_ptr)
        self.mlx.mlx_release(self.mlx_ptr)
