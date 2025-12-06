"""Depth-first search based maze generator."""

from __future__ import annotations

from random import Random
from typing import Iterable, List, Sequence, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]

MAZE_SIZE = 20


# List cells two steps away that we might carve toward.
def _neighbors(cell: Cell) -> Iterable[Cell]:
  row, col = cell
  deltas = ((0, 2), (0, -2), (2, 0), (-2, 0))
  for dr, dc in deltas:
    yield row + dr, col + dc


# Make sure a cell sits inside the maze border.
def _in_bounds(cell: Cell, max_row: int, max_col: int) -> bool:
  row, col = cell
  return 1 <= row < max_row - 1 and 1 <= col < max_col - 1


# Build a maze by carving passages with DFS backtracking.
def generate_maze(
  size: int = MAZE_SIZE,
  seed: int | None = None,
) -> Grid:
  if size < 2 or size % 2 != 0:
    raise ValueError("size must be an even integer greater than or equal to 2")

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
      neighbor
      for neighbor in _neighbors(current)
      if _in_bounds(neighbor, grid_span, grid_span) and neighbor not in visited
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

  # Ensure explicit exit opening at the goal.
  grid[goal[0]][goal[1]] = 0
  return grid


# Turn maze cells into a simple text view for debugging.
def maze_to_string(grid: Sequence[Sequence[int]]) -> str:
  return "\n".join("".join("#" if cell else " " for cell in row) for row in grid)


__all__ = ["generate_maze", "maze_to_string"]
