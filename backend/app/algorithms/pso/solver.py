"""Particle swarm optimizer that moves directly through the maze grid."""

from __future__ import annotations

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


def _fitness(cell: Cell, goal: Cell, steps: int, visited: int) -> float:
  distance = abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])
  base = 1.0 / (1 + distance)
  novelty = visited / max(1, steps)
  score = base + 0.1 * novelty
  if cell == goal:
    score += 10.0
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
) -> Tuple[List[Particle], Cell, Cell]:
  start, goal = _find_start_goal(maze)
  particles: List[Particle] = []
  for _ in range(swarm_size):
    jitter = (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3))
    position = (start[0] + jitter[0], start[1] + jitter[1])
    velocity = (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5))
    fitness = _fitness(start, goal, 1, 1)
    particles.append(
      Particle(
        position=position,
        velocity=velocity,
        cell=start,
        best_position=position,
        best_fitness=fitness,
        trace=[start],
        visited={start: 1},
      )
    )
  return particles, start, goal


def _discretize(position: Tuple[float, float], rows: int, cols: int) -> Cell:
  r = int(round(position[0]))
  c = int(round(position[1]))
  r = max(0, min(rows - 1, r))
  c = max(0, min(cols - 1, c))
  return r, c


def _step_toward(current: Cell, target: Cell, maze: Grid, rng: Random) -> Cell:
  rows = len(maze)
  cols = len(maze[0])
  options: List[Cell] = []
  dr = target[0] - current[0]
  dc = target[1] - current[1]
  candidates = []
  if dr != 0:
    step = 1 if dr > 0 else -1
    candidates.append((current[0] + step, current[1]))
  if dc != 0:
    step = 1 if dc > 0 else -1
    candidates.append((current[0], current[1] + step))
  rng.shuffle(candidates)
  for cell in candidates:
    if _in_bounds(cell, rows, cols) and maze[cell[0]][cell[1]] == 0:
      options.append(cell)
  if options:
    return options[0]
  return current


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
  particles, start, goal = _initialize_particles(maze, swarm_size, rng)
  global_best = max(particles, key=lambda p: p.best_fitness)

  inertia = 0.5
  cognitive = 1.5
  social = 1.75
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
      target_cell = _discretize(particle.position, rows, cols)
      if maze[target_cell[0]][target_cell[1]] == 1:
        target_cell = particle.cell

      new_cell = _step_toward(particle.cell, target_cell, maze, rng)
      if new_cell != particle.cell:
        particle.cell = new_cell
        particle.trace.append(new_cell)
        particle.visited[new_cell] = particle.visited.get(new_cell, 0) + 1

      fitness = _fitness(
        particle.cell,
        goal,
        len(particle.trace),
        len(particle.visited),
      )
      improved = False
      if fitness > particle.best_fitness:
        particle.best_fitness = fitness
        particle.best_position = particle.position
        particle.trace = particle.trace[-rows * cols :]
        improved = True

      if fitness > global_best.best_fitness:
        global_best = Particle(
          position=particle.position[:],
          velocity=particle.velocity[:],
          cell=particle.cell,
          best_position=particle.best_position[:],
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
