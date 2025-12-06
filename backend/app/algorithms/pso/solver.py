"""Simple PSO solver that searches for an order of DFS moves to solve a maze."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Iterable, List, Sequence, Tuple

Grid = Sequence[Sequence[int]]
Cell = Tuple[int, int]
Path = List[Cell]

DIRECTIONS: Tuple[Cell, ...] = (
  (0, 1),  # Right
  (1, 0),  # Down
  (0, -1),  # Left
  (-1, 0),  # Up
)


# Locate the first open cell and last open cell to use as start and goal.
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


# Check if a cell is inside the grid limits.
def _in_bounds(cell: Cell, rows: int, cols: int) -> bool:
  return 0 <= cell[0] < rows and 0 <= cell[1] < cols


# Measure how far two cells are using Manhattan distance.
def _manhattan(a: Cell, b: Cell) -> int:
  return abs(a[0] - b[0]) + abs(a[1] - b[1])


# Yield neighbors in the order prescribed by the particle weights.
def _neighbor_cells(cell: Cell, order: Sequence[int]) -> Iterable[Cell]:
  for idx in order:
    dr, dc = DIRECTIONS[idx]
    yield cell[0] + dr, cell[1] + dc


# Run DFS using a specific direction order and track best partial path.
def _depth_first_with_order(maze: Grid, order: Sequence[int]) -> Tuple[Path, bool]:
  rows = len(maze)
  cols = len(maze[0])
  start, goal = _find_start_goal(maze)

  stack: List[Tuple[Cell, Path]] = [(start, [start])]
  visited = {start}
  best_partial = [start]

  while stack:
    current, path = stack.pop()

    if _manhattan(current, goal) < _manhattan(best_partial[-1], goal):
      best_partial = path

    if current == goal:
      return path, True

    for neighbor in _neighbor_cells(current, order):
      if not _in_bounds(neighbor, rows, cols):
        continue
      if maze[neighbor[0]][neighbor[1]] == 1:
        continue
      if neighbor in visited:
        continue
      visited.add(neighbor)
      stack.append((neighbor, path + [neighbor]))

  return best_partial, False


# Score an order by how quickly it solves or approaches the goal.
def _evaluate_order(maze: Grid, order: Sequence[int]) -> Tuple[float, Path, bool]:
  path, solved = _depth_first_with_order(maze, order)
  start, goal = _find_start_goal(maze)
  if solved:
    fitness = 1000.0 - len(path)
  else:
    distance = _manhattan(path[-1], goal)
    fitness = -float(distance + len(path))
  return fitness, path, solved


@dataclass
class Particle:
  weights: List[float]
  velocity: List[float]
  best_weights: List[float]
  best_fitness: float
  best_path: Path
  solved: bool


# Convert weight values to a sorted direction preference.
def _order_from_weights(weights: Sequence[float]) -> List[int]:
  return sorted(range(len(weights)), key=lambda idx: weights[idx], reverse=True)


# Create the initial swarm with random priorities and velocities.
def _initialize_particles(
  maze: Grid, swarm_size: int, rng: Random
) -> List[Particle]:
  particles: List[Particle] = []
  for _ in range(swarm_size):
    weights = [rng.uniform(-1, 1) for _ in DIRECTIONS]
    velocity = [rng.uniform(-0.5, 0.5) for _ in DIRECTIONS]
    order = _order_from_weights(weights)
    fitness, path, solved = _evaluate_order(maze, order)
    particles.append(
      Particle(
        weights=weights[:],
        velocity=velocity[:],
        best_weights=weights[:],
        best_fitness=fitness,
        best_path=path,
        solved=solved,
      )
    )
  return particles


# Main entry that runs PSO to look for a maze path.
def solve_maze_with_pso(
  maze: Grid,
  iterations: int = 40,
  swarm_size: int = 12,
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
  particles = _initialize_particles(maze, swarm_size, rng)
  global_best = max(particles, key=lambda p: p.best_fitness)

  inertia = 0.7
  cognitive = 1.5
  social = 1.5

  history: List[dict] = []

  for iteration in range(iterations):
    for particle in particles:
      new_velocity: List[float] = []
      new_weights: List[float] = []
      for idx in range(len(DIRECTIONS)):
        r1 = rng.random()
        r2 = rng.random()
        vel = (
          inertia * particle.velocity[idx]
          + cognitive * r1 * (particle.best_weights[idx] - particle.weights[idx])
          + social * r2 * (global_best.best_weights[idx] - particle.weights[idx])
        )
        new_velocity.append(vel)
        new_weights.append(particle.weights[idx] + vel)

      particle.velocity = new_velocity
      particle.weights = new_weights

      order = _order_from_weights(particle.weights)
      fitness, path, solved = _evaluate_order(maze, order)

      if fitness > particle.best_fitness:
        particle.best_fitness = fitness
        particle.best_weights = particle.weights[:]
        particle.best_path = path
        particle.solved = solved

      if fitness > global_best.best_fitness:
        global_best = Particle(
          weights=particle.weights[:],
          velocity=particle.velocity[:],
          best_weights=particle.best_weights[:],
          best_fitness=fitness,
          best_path=path,
          solved=solved,
        )

    if capture_history:
      history.append(
        {
          "iteration": iteration,
          "best_fitness": global_best.best_fitness,
          "solved": global_best.solved,
          "path": list(global_best.best_path),
          "direction_order": _order_from_weights(global_best.best_weights),
        }
      )
    if global_best.solved:
      break

  start, goal = _find_start_goal(maze)
  result = {
    "solved": global_best.solved,
    "start": start,
    "goal": goal,
    "iterations": iterations,
    "swarm_size": swarm_size,
    "best_fitness": global_best.best_fitness,
    "path": global_best.best_path,
    "direction_order": _order_from_weights(global_best.best_weights),
  }
  if capture_history:
    result["history"] = history
  return result
