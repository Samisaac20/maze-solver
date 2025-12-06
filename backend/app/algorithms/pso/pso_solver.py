"""Particle swarm optimizer that moves directly through the maze grid."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
from numpy.random import Generator, default_rng

Grid = Sequence[Sequence[int]]
Cell = Tuple[int, int]
Path = List[Cell]

DIRECTIONS: Tuple[Cell, ...] = (
  (0, 1),  # Right
  (1, 0),  # Down
  (0, -1),  # Left
  (-1, 0),  # Up
)

VELOCITY_CLAMP = 1.2
MOVES_PER_ITERATION = 3


def _find_start_goal(maze: Grid) -> Tuple[Cell, Cell]:
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
    raise ValueError("maze must expose at least one open cell for start/goal detection")
  return start, goal


def _in_bounds(cell: Cell, rows: int, cols: int) -> bool:
  return 0 <= cell[0] < rows and 0 <= cell[1] < cols


def _build_distance_map(maze: Grid, goal: Cell) -> List[List[int]]:
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
      if not _in_bounds((nr, nc), rows, cols):
        continue
      if maze[nr][nc] == 1:
        continue
      if dist[nr][nc] > dist[row][col] + 1:
        dist[nr][nc] = dist[row][col] + 1
        queue.append((nr, nc))
  return dist


def _fitness(
  cell: Cell,
  goal: Cell,
  steps: int,
  visit_counts: Dict[Cell, int],
  distance_map: List[List[int]],
) -> float:
  distance = distance_map[cell[0]][cell[1]]
  base = 1.0 / (1 + distance)
  diversity = len(visit_counts) / max(1, steps)
  loop_penalty = 0.05 * visit_counts.get(cell, 0)
  score = base + 0.15 * diversity - loop_penalty
  if cell == goal:
    score += 15.0
  return score


def _serialize_path(path: Path) -> List[List[int]]:
  return [[row, col] for row, col in path]


@dataclass
class ParticleState:
  cell: Cell
  trace: Path
  visited: Dict[Cell, int]
  best_trace: Path
  best_fitness: float
  stagnation: int = 0
  solved: bool = False


def _initialize_particles(
  swarm_size: int,
  start: Cell,
  goal: Cell,
  distance_map: List[List[int]],
  rng: Generator,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[ParticleState]]:
  base = np.array(start, dtype=float)
  positions = base + rng.uniform(-0.3, 0.3, size=(swarm_size, 2))
  velocities = rng.uniform(-0.5, 0.5, size=(swarm_size, 2))
  best_positions = positions.copy()
  best_fitness = np.empty(swarm_size)

  states: List[ParticleState] = []
  for idx in range(swarm_size):
    visited = {start: 1}
    fitness = _fitness(start, goal, 1, visited, distance_map)
    state = ParticleState(
      cell=start,
      trace=[start],
      visited=visited,
      best_trace=[start],
      best_fitness=fitness,
    )
    states.append(state)
    best_fitness[idx] = fitness
  return positions, velocities, best_positions, best_fitness, states


def _choose_next_cell(
  current: Cell,
  velocity: Tuple[float, float],
  maze: Grid,
  distance_map: List[List[int]],
  rng: Generator,
) -> Cell:
  rows = len(maze)
  cols = len(maze[0])
  candidates: List[Tuple[float, Cell]] = []
  for dr, dc in DIRECTIONS:
    cell = (current[0] + dr, current[1] + dc)
    if not _in_bounds(cell, rows, cols):
      continue
    if maze[cell[0]][cell[1]] == 1:
      continue
    alignment = velocity[0] * dr + velocity[1] * dc
    heuristic = -distance_map[cell[0]][cell[1]]
    score = alignment + 0.3 * heuristic + rng.uniform(-0.05, 0.05)
    candidates.append((score, cell))

  if not candidates:
    return current
  candidates.sort(key=lambda item: item[0], reverse=True)
  exploration = rng.random()
  if exploration < 0.15 and len(candidates) > 1:
    selected = rng.choice([cell for _, cell in candidates[1:]])
  else:
    selected = candidates[0][1]
  return (int(selected[0]), int(selected[1]))


def _path_solved(path: Path, goal: Cell) -> bool:
  return bool(path) and path[-1] == goal


def solve_maze_with_pso(
  maze: Grid,
  iterations: int = 80,
  swarm_size: int = 30,
  seed: int | None = None,
  capture_history: bool = False,
) -> dict:
  if iterations <= 0:
    raise ValueError("iterations must be positive")
  if swarm_size <= 0:
    raise ValueError("swarm_size must be positive")
  if not maze or not maze[0]:
    raise ValueError("maze must contain at least one row and one column")

  rng = default_rng(seed)
  start, goal = _find_start_goal(maze)
  distance_map = _build_distance_map(maze, goal)
  (
    positions,
    velocities,
    best_positions,
    best_fitness,
    states,
  ) = _initialize_particles(swarm_size, start, goal, distance_map, rng)

  global_best_idx = int(np.argmax(best_fitness))
  rows = len(maze)
  cols = len(maze[0])
  stagnation_limit = max(1, iterations // 4)

  inertia = 0.55
  cognitive = 1.6
  social = 1.8

  history: List[dict] = []

  for iteration in range(iterations):
    r1 = rng.random((swarm_size, 1))
    r2 = rng.random((swarm_size, 1))
    global_best_position = best_positions[global_best_idx]
    velocities = (
      inertia * velocities
      + cognitive * r1 * (best_positions - positions)
      + social * r2 * (global_best_position - positions)
    )
    np.clip(velocities, -VELOCITY_CLAMP, VELOCITY_CLAMP, out=velocities)
    positions += velocities

    iteration_particles: List[dict] = []
    for idx, state in enumerate(states):
      velocity_vector = tuple(velocities[idx])
      for _ in range(MOVES_PER_ITERATION):
        next_cell = _choose_next_cell(
          state.cell,
          velocity_vector,
          maze,
          distance_map,
          rng,
        )
        if next_cell != state.cell:
          state.cell = next_cell
          state.trace.append(next_cell)
          if len(state.trace) > rows * cols:
            state.trace.pop(0)
          state.visited[next_cell] = state.visited.get(next_cell, 0) + 1
        if next_cell == goal:
          break

      fitness = _fitness(
        state.cell,
        goal,
        len(state.trace),
        state.visited,
        distance_map,
      )
      improved = fitness > best_fitness[idx]
      if improved:
        best_fitness[idx] = fitness
        best_positions[idx] = positions[idx]
        state.best_fitness = fitness
        state.best_trace = state.trace[-rows * cols :].copy()

      state.solved = state.cell == goal
      state.stagnation = 0 if improved else state.stagnation + 1

      if state.stagnation >= stagnation_limit:
        positions[idx] = np.array(start, dtype=float) + rng.uniform(-0.3, 0.3, size=2)
        velocities[idx] = rng.uniform(-0.5, 0.5, size=2)
        state.cell = start
        state.trace = [start]
        state.visited = {start: 1}
        state.best_trace = [start]
        state.best_fitness = _fitness(start, goal, 1, state.visited, distance_map)
        best_positions[idx] = positions[idx]
        best_fitness[idx] = state.best_fitness
        state.stagnation = 0
        state.solved = False

      if capture_history:
        iteration_particles.append(
          {
            "index": idx,
            "path": _serialize_path(state.trace),
            "fitness": fitness,
            "solved": state.solved,
          }
        )

    global_best_idx = int(np.argmax(best_fitness))

    if capture_history:
      history.append(
        {
          "iteration": iteration,
          "particles": iteration_particles,
          "global_best": {
            "path": _serialize_path(states[global_best_idx].best_trace),
            "fitness": float(best_fitness[global_best_idx]),
            "solved": _path_solved(states[global_best_idx].best_trace, goal),
          },
        }
      )

    if _path_solved(states[global_best_idx].best_trace, goal):
      break

  best_state = states[global_best_idx]
  result = {
    "solved": _path_solved(best_state.best_trace, goal),
    "start": start,
    "goal": goal,
    "iterations": iterations,
    "swarm_size": swarm_size,
    "best_fitness": float(best_fitness[global_best_idx]),
    "path": _serialize_path(best_state.best_trace),
  }
  if capture_history:
    result["history"] = history
  return result
