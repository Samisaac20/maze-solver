"""Shared helpers for GA maze exploration."""

from __future__ import annotations

from collections import deque
from random import Random
from typing import Dict, List, Sequence, Tuple

Grid = Sequence[Sequence[int]]
Cell = Tuple[int, int]
Path = List[Cell]

DIRECTIONS: Tuple[Cell, ...] = (
  (-1, 0),
  (1, 0),
  (0, -1),
  (0, 1),
)


def find_start_goal(maze: Grid) -> Tuple[Cell, Cell]:
  rows = len(maze)
  cols = len(maze[0])
  start = None
  goal = None
  for r in range(rows):
    for c in range(cols):
      if maze[r][c] == 0:
        start = (r, c)
        break
    if start:
      break
  for r in range(rows - 1, -1, -1):
    for c in range(cols - 1, -1, -1):
      if maze[r][c] == 0:
        goal = (r, c)
        break
    if goal:
      break
  if start is None or goal is None:
    raise ValueError("maze must expose start and goal cells")
  return start, goal


def _in_bounds(cell: Cell, rows: int, cols: int) -> bool:
  return 0 <= cell[0] < rows and 0 <= cell[1] < cols


def build_distance_map(maze: Grid, goal: Cell) -> List[List[int]]:
  rows = len(maze)
  cols = len(maze[0])
  dist = [[10**9 for _ in range(cols)] for _ in range(rows)]
  queue: deque[Cell] = deque()
  dist[goal[0]][goal[1]] = 0
  queue.append(goal)
  while queue:
    row, col = queue.popleft()
    for dr, dc in DIRECTIONS:
      nr, nc = row + dr, col + dc
      if not _in_bounds((nr, nc), rows, cols) or maze[nr][nc] == 1:
        continue
      if dist[nr][nc] > dist[row][col] + 1:
        dist[nr][nc] = dist[row][col] + 1
        queue.append((nr, nc))
  return dist


def build_adjacency(maze: Grid) -> Dict[Cell, List[Cell]]:
  rows = len(maze)
  cols = len(maze[0])
  adjacency: Dict[Cell, List[Cell]] = {}
  for r in range(rows):
    for c in range(cols):
      if maze[r][c] == 1:
        continue
      cell = (r, c)
      neighbors: List[Cell] = []
      for dr, dc in DIRECTIONS:
        nxt = (r + dr, c + dc)
        if _in_bounds(nxt, rows, cols) and maze[nxt[0]][nxt[1]] == 0:
          neighbors.append(nxt)
      adjacency[cell] = neighbors
  return adjacency


def simplify_path(path: Path) -> Path:
  simplified: Path = []
  positions: Dict[Cell, int] = {}
  for cell in path:
    if cell in positions:
      remove_from = positions[cell] + 1
      while len(simplified) > remove_from:
        removed = simplified.pop()
        positions.pop(removed, None)
    else:
      simplified.append(cell)
      positions[cell] = len(simplified) - 1
  return simplified


def biased_step(
  rng: Random,
  current: Cell,
  adjacency: Dict[Cell, List[Cell]],
  distance_map: List[List[int]],
) -> Cell | None:
  neighbors = adjacency.get(current)
  if not neighbors:
    return None
  weights = [
    1.0 / (1 + distance_map[neighbor[0]][neighbor[1]])
    for neighbor in neighbors
  ]
  total = sum(weights)
  if total == 0:
    return rng.choice(neighbors)
  cumulative = 0.0
  target = rng.random()
  for neighbor, weight in zip(neighbors, weights):
    probability = weight / total
    cumulative += probability
    if target <= cumulative:
      return neighbor
  return neighbors[-1]


def random_path(
  rng: Random,
  start: Cell,
  goal: Cell,
  adjacency: Dict[Cell, List[Cell]],
  distance_map: List[List[int]],
  max_steps: int,
) -> Path:
  path: Path = [start]
  current = start
  for _ in range(max_steps):
    if current == goal:
      break
    next_cell = biased_step(rng, current, adjacency, distance_map)
    if next_cell is None:
      break
    current = next_cell
    path.append(current)
  return simplify_path(path)


def greedy_path_to_goal(
  start: Cell,
  goal: Cell,
  adjacency: Dict[Cell, List[Cell]],
  distance_map: List[List[int]],
) -> Path:
  if distance_map[start[0]][start[1]] >= 10**9:
    return [start]
  path: Path = [start]
  current = start
  visited: set[Cell] = {start}
  while current != goal:
    neighbors = adjacency.get(current)
    if not neighbors:
      break
    neighbors.sort(key=lambda cell: distance_map[cell[0]][cell[1]])
    for neighbor in neighbors:
      if neighbor not in visited and distance_map[neighbor[0]][neighbor[1]] < distance_map[current[0]][current[1]]:
        path.append(neighbor)
        visited.add(neighbor)
        current = neighbor
        break
    else:
      break
  return path


__all__ = [
  "Grid",
  "Cell",
  "Path",
  "DIRECTIONS",
  "find_start_goal",
  "build_distance_map",
  "build_adjacency",
  "simplify_path",
  "biased_step",
  "random_path",
  "greedy_path_to_goal",
]
