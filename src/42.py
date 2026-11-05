from .maze_generator import Point


DIGIT_FOUR: tuple[tuple[int, ...], ...] = (
    (1, 0, 1),
    (1, 0, 1),
    (1, 1, 1),
    (0, 0, 1),
    (0, 0, 1),
)

DIGIT_TWO: tuple[tuple[int, ...], ...] = (
    (1, 1, 1),
    (0, 0, 1),
    (1, 1, 1),
    (1, 0, 0),
    (1, 1, 1),
)

DIGIT_GAP = 1
PATTERN_42_WIDTH = len(DIGIT_FOUR[0]) + DIGIT_GAP + len(DIGIT_TWO[0])
PATTERN_42_HEIGHT = len(DIGIT_FOUR)


def cells_from_bitmap(
    bitmap: tuple[tuple[int, ...], ...],
    origin: Point,
) -> set[Point]:
    cells: set[Point] = set()
    for dy, row in enumerate(bitmap):
        for dx, bit in enumerate(row):
            if bit:
                cells.add(Point(origin.x + dx, origin.y + dy))
    return cells


def pattern_42_origin(width: int, height: int) -> Point:
    return Point(
        (width - PATTERN_42_WIDTH) // 2,
        (height - PATTERN_42_HEIGHT) // 2,
    )


def pattern_42_candidate_origins(width: int, height: int) -> list[Point]:
    """Return every fitting origin, ordered from the maze centre outward."""
    max_x = width - PATTERN_42_WIDTH
    max_y = height - PATTERN_42_HEIGHT
    if max_x < 0 or max_y < 0:
        return []

    origins = [
        Point(x, y)
        for y in range(max_y + 1)
        for x in range(max_x + 1)
    ]
    origins.sort(
        key=lambda origin: (
            abs(2 * origin.x - max_x) + abs(2 * origin.y - max_y),
            origin.y,
            origin.x,
        )
    )
    return origins


def pattern_42_cells(origin: Point) -> set[Point]:
    four = cells_from_bitmap(DIGIT_FOUR, origin)
    two = cells_from_bitmap(
        DIGIT_TWO,
        Point(origin.x + len(DIGIT_FOUR[0]) + DIGIT_GAP, origin.y),
    )
    return four | two


def non_perfect_key_cells(width: int, height: int) -> set[Point]:
    """Cells that must remain corridors for Pac-Man-like mazes."""
    return {
        Point(0, 0),
        Point(width - 1, 0),
        Point(0, height - 1),
        Point(width - 1, height - 1),
        Point(width // 2, height // 2),
    }


def get_42_cells(
    width: int,
    height: int,
    start: Point | None = None,
    end: Point | None = None,
    perfect: bool = True,
) -> set[Point] | None:
    """Choose a placement that does not cover required corridor cells."""
    if width < PATTERN_42_WIDTH or height < PATTERN_42_HEIGHT:
        print(
            f"Maze {width}x{height} is too small for the '42' pattern "
            f"(needs at least {PATTERN_42_WIDTH}x{PATTERN_42_HEIGHT}); "
            "omitting it."
        )
        return None

    forbidden = {point for point in (start, end) if point is not None}
    if not perfect:
        forbidden.update(non_perfect_key_cells(width, height))

    preferred = pattern_42_origin(width, height)
    for origin in pattern_42_candidate_origins(width, height):
        cells = pattern_42_cells(origin)
        if cells & forbidden:
            continue
        if origin != preferred:
            print(
                f"'42' pattern shifted to ({origin.x},{origin.y}) "
                "to keep required corridor cells free."
            )
        return cells

    print(
        "Cannot place the '42' pattern without covering required cells; "
        "omitting it."
    )
    return None
