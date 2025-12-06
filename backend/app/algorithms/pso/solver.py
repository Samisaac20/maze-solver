"""Particle swarm optimizer that moves directly through the maze grid."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from random import Random
from typing import Dict, List, Sequence, Tuple

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
class Particle:
  position: Tuple[float, float]
  velocity: Tuple[float, float]
  cell: Cell
  best_position: Tuple[float, float]
  best_fitness: float
  trace: Path
  visited: Dict[Cell, int]
  stagnation: int = 0
  solved: bool = False


def _initialize_particles(
  maze: Grid,
  swarm_size: int,
  rng: Random,
  start: Cell,
  goal: Cell,
  distance_map: List[List[int]],
) -> List[Particle]:
  particles: List[Particle] = []
  for _ in range(swarm_size):
    jitter = (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3))
    position = (start[0] + jitter[0], start[1] + jitter[1])
    velocity = (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5))
    visited = {start: 1}
    fitness = _fitness(start, goal, 1, visited, distance_map)
    particles.append(
      Particle(
        position=position,
        velocity=velocity,
        cell=start,
        best_position=position,
        best_fitness=fitness,
        trace=[start],
        visited=visited,
      )
    )
  return particles


def _discretize(position: Tuple[float, float], rows: int, cols: int) -> Cell:
  r = int(round(position[0]))
  c = int(round(position[1]))
  r = max(0, min(rows - 1, r))
  c = max(0, min(cols - 1, c))
  return r, c


def _choose_next_cell(
  current: Cell,
  velocity: Tuple[float, float],
  maze: Grid,
  distance_map: List[List[int]],
  rng: Random,
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
    return rng.choice([cell for _, cell in candidates[1:]])
  return candidates[0][1]


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

  rng = Random(seed)
  start, goal = _find_start_goal(maze)
  distance_map = _build_distance_map(maze, goal)
  particles = _initialize_particles(maze, swarm_size, rng, start, goal, distance_map)
  global_best = max(particles, key=lambda p: p.best_fitness)

  inertia = 0.55
  cognitive = 1.6
  social = 1.8
  rows = len(maze)
  cols = len(maze[0])
  stagnation_limit = iterations // 4 or 1

  history: List[dict] = []

  for iteration in range(iterations):
    iteration_particles: List[dict] = []

    for idx, particle in enumerate(particles):
      r1 = rng.random()
      r2 = rng.random()
      vx = (
        inertia * particle.velocity[0]
        + cognitive * r1 * (particle.best_position[0] - particle.position[0])
        + social * r2 * (global_best.best_position[0] - particle.position[0])
      )
      vy = (
        inertia * particle.velocity[1]
        + cognitive * r1 * (particle.best_position[1] - particle.position[1])
        + social * r2 * (global_best.best_position[1] - particle.position[1])
      )
      vx = max(-VELOCITY_CLAMP, min(VELOCITY_CLAMP, vx))
      vy = max(-VELOCITY_CLAMP, min(VELOCITY_CLAMP, vy))

      particle.velocity = (vx, vy)
      particle.position = (particle.position[0] + vx, particle.position[1] + vy)
      for _ in range(MOVES_PER_ITERATION):
        next_cell = _choose_next_cell(
          particle.cell,
          particle.velocity,
          maze,
          distance_map,
          rng,
        )
        if next_cell != particle.cell:
          particle.cell = next_cell
          particle.trace.append(next_cell)
          particle.visited[next_cell] = particle.visited.get(next_cell, 0) + 1
        if particle.cell == goal:
          break

      fitness = _fitness(
        particle.cell,
        goal,
        len(particle.trace),
        particle.visited,
        distance_map,
      )
      improved = False
      if fitness > particle.best_fitness:
        particle.best_fitness = fitness
        particle.best_position = particle.position
        particle.trace = particle.trace[-rows * cols :]
        improved = True

      if fitness > global_best.best_fitness:
        global_best = Particle(
          position=particle.position,
          velocity=particle.velocity,
          cell=particle.cell,
          best_position=particle.best_position,
          best_fitness=particle.best_fitness,
          trace=particle.trace[:],
          visited=particle.visited.copy(),
          solved=particle.cell == goal,
        )

      particle.solved = particle.cell == goal
      particle.stagnation = 0 if improved else particle.stagnation + 1

      if particle.stagnation >= stagnation_limit:
        jitter = (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3))
        particle.position = (start[0] + jitter[0], start[1] + jitter[1])
        particle.cell = start
        particle.velocity = (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5))
        particle.trace = [start]
        particle.visited = {start: 1}
        particle.stagnation = 0
        particle.best_fitness = _fitness(start, goal, 1, particle.visited, distance_map)
        particle.best_position = particle.position

      if capture_history:
        iteration_particles.append(
          {
            "index": idx,
            "path": _serialize_path(particle.trace),
            "fitness": fitness,
            "solved": particle.solved,
          }
        )

    if capture_history:
      history.append(
        {
          "iteration": iteration,
          "particles": iteration_particles,
          "global_best": {
            "path": _serialize_path(global_best.trace),
            "fitness": global_best.best_fitness,
            "solved": global_best.solved,
          },
        }
      )

    if global_best.solved:
      break

  result = {
    "solved": global_best.solved,
    "start": start,
    "goal": goal,
    "iterations": iterations,
    "swarm_size": swarm_size,
    "best_fitness": global_best.best_fitness,
    "path": _serialize_path(global_best.trace),
  }
  if capture_history:
    result["history"] = history
  return result
