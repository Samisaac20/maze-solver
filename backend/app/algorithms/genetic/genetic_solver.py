"""Genetic algorithm based maze solver with visualisation history."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from random import Random
from typing import Dict, List, Sequence, Tuple

Grid = Sequence[Sequence[int]]
Cell = Tuple[int, int]
Path = List[Cell]
Chromosome = List[int]

DIRECTIONS: Tuple[Cell, ...] = (
  (-1, 0),  # Up
  (1, 0),  # Down
  (0, -1),  # Left
  (0, 1),  # Right
)
VISUAL_PATH_LIMIT = 600
HISTORY_SAMPLE_LIMIT = 24


@dataclass
class SimulationResult:
  path: Path
  visited_unique: int
  collisions: int
  final_cell: Cell
  best_distance: int
  solved: bool


@dataclass
class Individual:
  index: int
  genes: Chromosome
  fitness: float
  solved: bool
  path: Path


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
    raise ValueError("maze must expose start and goal cells")
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
      if not _in_bounds((nr, nc), rows, cols) or maze[nr][nc] == 1:
        continue
      if dist[nr][nc] > dist[row][col] + 1:
        dist[nr][nc] = dist[row][col] + 1
        queue.append((nr, nc))
  return dist


def _simulate_chromosome(
  genes: Chromosome,
  maze: Grid,
  start: Cell,
  goal: Cell,
  distance_map: List[List[int]],
) -> SimulationResult:
  rows = len(maze)
  cols = len(maze[0])
  cell = start
  path: Path = [start]
  visited: Dict[Cell, int] = {start: 1}
  collisions = 0
  best_distance = distance_map[start[0]][start[1]]
  solved = False

  for direction_idx in genes:
    dr, dc = DIRECTIONS[direction_idx % len(DIRECTIONS)]
    next_cell = (cell[0] + dr, cell[1] + dc)
    if not _in_bounds(next_cell, rows, cols) or maze[next_cell[0]][next_cell[1]] == 1:
      collisions += 1
      continue
    cell = next_cell
    path.append(cell)
    visited[cell] = visited.get(cell, 0) + 1
    cell_distance = distance_map[cell[0]][cell[1]]
    if cell_distance < best_distance:
      best_distance = cell_distance
    if cell == goal:
      solved = True
      break

  return SimulationResult(
    path=path,
    visited_unique=len(visited),
    collisions=collisions,
    final_cell=cell,
    best_distance=0 if solved else best_distance,
    solved=solved,
  )


def _fitness(
  result: SimulationResult,
  distance_map: List[List[int]],
) -> float:
  distance = distance_map[result.final_cell[0]][result.final_cell[1]]
  distance_score = 1.0 / (1 + distance)
  progress_score = 1.0 / (1 + result.best_distance)
  coverage = result.visited_unique / max(1, len(result.path))
  collision_penalty = 0.02 * result.collisions
  score = 0.5 * progress_score + 0.5 * distance_score + 0.2 * coverage - collision_penalty
  if result.solved:
    score += 30.0 - 0.02 * len(result.path)
  return score


def _random_chromosome(rng: Random, length: int) -> Chromosome:
  return [rng.randrange(len(DIRECTIONS)) for _ in range(length)]


def _crossover(parent_a: Chromosome, parent_b: Chromosome, rng: Random) -> Chromosome:
  if len(parent_a) <= 1:
    return parent_a[:]
  point = rng.randrange(1, len(parent_a))
  return parent_a[:point] + parent_b[point:]


def _mutate(genes: Chromosome, rng: Random, rate: float) -> Chromosome:
  for idx in range(len(genes)):
    if rng.random() < rate:
      genes[idx] = rng.randrange(len(DIRECTIONS))
  return genes


def _tournament_select(
  population: List[Individual],
  rng: Random,
  tournament_size: int = 3,
) -> Individual:
  if len(population) <= tournament_size:
    contenders = population
  else:
    contenders = rng.sample(population, tournament_size)
  return max(contenders, key=lambda individual: individual.fitness)


def _serialize_path(path: Path, *, limit: int | None = None) -> List[List[int]]:
  subset = path if limit is None else path[:limit]
  return [[row, col] for row, col in subset]


def _snapshot_population(
  evaluated: List[Individual],
  rng: Random,
) -> List[dict]:
  if len(evaluated) <= HISTORY_SAMPLE_LIMIT:
    selected = evaluated
  else:
    top_count = HISTORY_SAMPLE_LIMIT // 2
    top = sorted(
      evaluated,
      key=lambda individual: individual.fitness,
      reverse=True,
    )[:top_count]
    top_ids = {id(ind) for ind in top}
    remainder = [ind for ind in evaluated if id(ind) not in top_ids]
    fill = HISTORY_SAMPLE_LIMIT - len(top)
    random_pick = rng.sample(remainder, fill)
    selected = top + random_pick
  return [
    {
      "index": individual.index,
      "path": _serialize_path(individual.path, limit=VISUAL_PATH_LIMIT),
      "fitness": individual.fitness,
      "solved": individual.solved,
    }
    for individual in selected
  ]


def solve_maze_with_genetic(
  maze: Grid,
  *,
  population_size: int = 80,
  generations: int = 120,
  mutation_rate: float = 0.08,
  capture_history: bool = False,
  seed: int | None = None,
) -> Dict[str, object]:
  if not maze or not maze[0]:
    raise ValueError("maze must contain at least one row and column")
  if population_size <= 0:
    raise ValueError("population_size must be positive")
  if generations <= 0:
    raise ValueError("generations must be positive")
  if not 0 <= mutation_rate <= 1:
    raise ValueError("mutation_rate must be between 0 and 1")

  rng = Random(seed)
  start, goal = _find_start_goal(maze)
  rows = len(maze)
  cols = len(maze[0])
  chromosome_length = max(rows * cols // 2, rows + cols)
  distance_map = _build_distance_map(maze, goal)

  population: List[Chromosome] = [
    _random_chromosome(rng, chromosome_length) for _ in range(population_size)
  ]
  best_overall: Individual | None = None
  history: List[dict] = []

  for generation in range(generations):
    evaluated: List[Individual] = []
    for index, genes in enumerate(population):
      simulation = _simulate_chromosome(genes, maze, start, goal, distance_map)
      fitness = _fitness(simulation, distance_map)
      evaluated.append(
        Individual(
          index=index,
          genes=genes,
          fitness=fitness,
          solved=simulation.solved,
          path=simulation.path,
        )
      )

    evaluated.sort(key=lambda individual: individual.fitness, reverse=True)
    if best_overall is None or evaluated[0].fitness > best_overall.fitness:
      best_overall = evaluated[0]

    if capture_history:
      population_snapshot = _snapshot_population(evaluated, rng)
      history.append(
        {
          "generation": generation,
          "population": population_snapshot,
          "best": {
            "index": evaluated[0].index,
            "path": _serialize_path(evaluated[0].path),
            "fitness": evaluated[0].fitness,
            "solved": evaluated[0].solved,
          },
        }
      )

    if evaluated[0].solved:
      best_overall = evaluated[0]
      break

    elite_count = max(1, population_size // 10)
    elites = [individual.genes[:] for individual in evaluated[:elite_count]]

    next_generation: List[Chromosome] = elites
    while len(next_generation) < population_size:
      parent_a = _tournament_select(evaluated, rng)
      parent_b = _tournament_select(evaluated, rng)
      child = _crossover(parent_a.genes, parent_b.genes, rng)
      child = _mutate(child, rng, mutation_rate)
      next_generation.append(child)

    population = next_generation

  assert best_overall is not None
  result = {
    "solver": "genetic_algorithm",
    "solved": best_overall.solved,
    "start": start,
    "goal": goal,
    "population_size": population_size,
    "generations": generations,
    "mutation_rate": mutation_rate,
    "best_fitness": best_overall.fitness,
    "path": _serialize_path(best_overall.path),
  }
  if capture_history:
    result["history"] = history
  return result
