from __future__ import annotations

from random import Random
from typing import Iterable, List, Sequence, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]

MAZE_SIZE = 30


def _neighbors(cell: Cell) -> Iterable[Cell]:
    row, col = cell
    for dr, dc in ((0,2),(0,-2),(2,0),(-2,0)):
        yield row + dr, col + dc


def _in_bounds(cell: Cell, max_row: int, max_col: int) -> bool:
    row, col = cell
    return 1 <= row < max_row - 1 and 1 <= col < max_col - 1


def _count_open_neighbors(cell: Cell, grid: Grid) -> int:
    r, c = cell
    count = 0
    for dr, dc in ((0,1),(0,-1),(1,0),( -1,0)):
        if grid[r+dr][c+dc] == 0:
            count += 1
    return count


def _find_dead_ends(grid: Grid) -> List[Cell]:
    out = []
    for r in range(1, len(grid)-1):
        for c in range(1, len(grid[0])-1):
            if grid[r][c] == 0 and _count_open_neighbors((r,c), grid) == 1:
                out.append((r,c))
    return out


def generate_maze(
    size: int = MAZE_SIZE,
    seed: int | None = None,
) -> Grid:
    if size < 5:
        raise ValueError("size must be at least 5")
    if size % 5 != 0:
        raise ValueError("size must be a multiple of 5 to keep width and height aligned")

    rng = Random(seed)
    grid_span = size * 2 + 1
    grid: Grid = [[1 for _ in range(grid_span)] for _ in range(grid_span)]

    start = (1, 1)
    goal = (grid_span - 2, grid_span - 2)
    grid[start[0]][start[1]] = 0
    grid[goal[0]][goal[1]] = 0

    stack: List[Cell] = [start]
    visited: set[Cell] = {start}

    while stack:
        current = stack[-1]
        available = [
            n for n in _neighbors(current)
            if _in_bounds(n, grid_span, grid_span) and n not in visited
        ]

        if not available:
            stack.pop()
            continue

        next_cell = rng.choice(available)
        wall = (
            current[0] + (next_cell[0] - current[0]) // 2,
            current[1] + (next_cell[1] - current[1]) // 2,
        )

        grid[wall[0]][wall[1]] = 0
        grid[next_cell[0]][next_cell[1]] = 0
        visited.add(next_cell)
        stack.append(next_cell)

    dead_ends = _find_dead_ends(grid)

    if len(dead_ends) < 2:
        need = 2 - len(dead_ends)
        attempts = 0
        while need > 0 and attempts < 500:
            attempts += 1
            r = rng.randrange(3, grid_span-3, 2)
            c = rng.randrange(3, grid_span-3, 2)
            if grid[r][c] != 0:
                continue
            dirs = [(0,2),(0,-2),(2,0),(-2,0)]
            rng.shuffle(dirs)
            for dr, dc in dirs:
                nr, nc = r+dr, c+dc
                if not _in_bounds((nr,nc), grid_span, grid_span):
                    continue
                if grid[nr][nc] == 0:
                    continue
                wr, wc = r + dr//2, c + dc//2
                grid[wr][wc] = 0
                grid[nr][nc] = 0
                new_dead = _find_dead_ends(grid)
                if len(new_dead) > len(dead_ends):
                    dead_ends = new_dead
                    need -= 1
                break

    return grid


def maze_to_string(grid: Sequence[Sequence[int]]) -> str:
    return "\n".join("".join("#" if cell else " " for cell in row) for row in grid)


__all__ = ["generate_maze", "maze_to_string"]
