"""Depth-first search based maze generator with enhanced branching."""

from __future__ import annotations

from random import Random
from typing import Iterable, List, Sequence, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]

MAZE_SIZE = 15


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


# Count how many neighbors of a cell have already been visited.
def _count_visited_neighbors(cell: Cell, visited: set[Cell], max_row: int, max_col: int) -> int:
  """Count visited neighbors to detect potential junction points."""
  count = 0
  for neighbor in _neighbors(cell):
    if _in_bounds(neighbor, max_row, max_row) and neighbor in visited:
      count += 1
  return count


# Build a maze by carving passages with DFS backtracking.
def generate_maze(
  size: int = MAZE_SIZE,
  seed: int | None = None,
  branch_bias: float = 0.35,
) -> Grid:
  """
  Generate a maze with enhanced branching structure.
  
  Args:
    size: Maze dimension parameter (must be ≥5 and divisible by 5)
    seed: Random seed for reproducibility
    branch_bias: Probability (0-1) of backtracking early to create branches.
                 Higher values = more branching. Recommended: 0.2-0.5
  """
  if size < 5:
    raise ValueError("size must be at least 5")
  if size % 5 != 0:
    raise ValueError("size must be a multiple of 5 to keep width and height aligned")
  if not 0 <= branch_bias <= 1:
    raise ValueError("branch_bias must be between 0 and 1")

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

    # KEY MODIFICATION 1: Shuffle neighbors to avoid directional bias
    rng.shuffle(available)
    
    # KEY MODIFICATION 2: Weighted selection favoring cells that create branches
    # Cells with fewer visited neighbors are at junction points, creating branches
    weights = []
    for neighbor in available:
      visited_count = _count_visited_neighbors(neighbor, visited, grid_span, grid_span)
      # Lower visited count = higher weight (creates more branches)
      # Add 1 to avoid zero weights
      weight = 4 - visited_count + 1
      weights.append(weight)
    
    # Use weighted random selection
    next_cell = rng.choices(available, weights=weights, k=1)[0]
    
    wall = (
      current[0] + (next_cell[0] - current[0]) // 2,
      current[1] + (next_cell[1] - current[1]) // 2,
    )

    grid[wall[0]][wall[1]] = 0
    grid[next_cell[0]][next_cell[1]] = 0
    visited.add(next_cell)
    stack.append(next_cell)
    
    # KEY MODIFICATION 3: Randomly backtrack early to encourage branching
    # This prevents long corridors by occasionally jumping to earlier junctions
    if len(stack) > 2 and rng.random() < branch_bias:
      # Pop current cell to backtrack and explore alternative paths
      stack.pop()

  # Ensure explicit exit opening at the goal.
  grid[goal[0]][goal[1]] = 0
  return grid


# Turn maze cells into a simple text view for debugging.
def maze_to_string(grid: Sequence[Sequence[int]]) -> str:
  return "\n".join("".join("#" if cell else " " for cell in row) for row in grid)


__all__ = ["generate_maze", "maze_to_string"]