"""Placeholder implementation for the Ant Colony Optimization solver."""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

Grid = Sequence[Sequence[int]]
Cell = Tuple[int, int]

PLACEHOLDER_MESSAGE = "Ant Colony Optimization solver is coming soon."


def _maze_shape(maze: Grid) -> list[int]:
  rows = len(maze)
  cols = len(maze[0]) if rows else 0
  return [rows, cols]


def _base_payload(
  maze: Grid,
  *,
  ants: int,
  evaporation_rate: float,
  history_requested: bool,
) -> Dict[str, object]:
  return {
    "solver": "ant_colony",
    "implemented": False,
    "message": PLACEHOLDER_MESSAGE,
    "maze_shape": _maze_shape(maze),
    "ants": ants,
    "evaporation_rate": evaporation_rate,
    "history": [] if history_requested else None,
  }


def solve_maze_with_ant_colony(
  maze: Grid,
  *,
  ants: int = 80,
  evaporation_rate: float = 0.5,
  capture_history: bool = False,
) -> Dict[str, object]:
  """Return a placeholder payload the frontend can render until ACO is implemented."""
  return _base_payload(
    maze,
    ants=ants,
    evaporation_rate=evaporation_rate,
    history_requested=capture_history,
  )
