"""Placeholder for the Firefly Algorithm maze solver."""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

Grid = Sequence[Sequence[int]]
Cell = Tuple[int, int]

PLACEHOLDER_MESSAGE = "Firefly Algorithm solver is coming soon."


def _maze_shape(maze: Grid) -> list[int]:
  rows = len(maze)
  cols = len(maze[0]) if rows else 0
  return [rows, cols]


def _base_payload(maze: Grid, *, fireflies: int, absorption: float, history_requested: bool) -> Dict[str, object]:
  return {
    "solver": "firefly_algorithm",
    "implemented": False,
    "message": PLACEHOLDER_MESSAGE,
    "maze_shape": _maze_shape(maze),
    "fireflies": fireflies,
    "absorption": absorption,
    "history": [] if history_requested else None,
  }


def solve_maze_with_firefly(
  maze: Grid,
  *,
  fireflies: int = 60,
  absorption: float = 1.0,
  capture_history: bool = False,
) -> Dict[str, object]:
  """Return a placeholder payload so the frontend can display forthcoming Firefly visuals."""
  return _base_payload(
    maze,
    fireflies=fireflies,
    absorption=absorption,
    history_requested=capture_history,
  )
