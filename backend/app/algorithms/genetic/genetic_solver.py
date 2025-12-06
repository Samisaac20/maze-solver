"""Genetic algorithm based maze solver with visualisation history."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Dict, List

from .path_utils import (
  Cell,
  Grid,
  Path,
  build_adjacency,
  build_distance_map,
  find_start_goal,
  greedy_path_to_goal,
  random_path,
  simplify_path,
  biased_step,
)

Chromosome = Path
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


def _evaluate_path(
  path: Path,
  goal: Cell,
  distance_map: List[List[int]],
) -> SimulationResult:
  if not path:
    raise ValueError("path must contain at least one cell")
  simplified_path = simplify_path(path)
  final_cell = simplified_path[-1]
  visited_unique = len({cell for cell in simplified_path})
  best_distance = min(distance_map[cell[0]][cell[1]] for cell in simplified_path)
  return SimulationResult(
    path=simplified_path,
    visited_unique=visited_unique,
    collisions=0,
    final_cell=final_cell,
    best_distance=best_distance,
    solved=final_cell == goal,
  )


def _fitness(result: SimulationResult, distance_map: List[List[int]]) -> float:
  distance = distance_map[result.final_cell[0]][result.final_cell[1]]
  distance_score = 1.0 / (1 + distance)
  progress_score = 1.0 / (1 + result.best_distance)
  coverage = result.visited_unique / max(1, len(result.path))
  path_efficiency = 1.0 / max(1, len(result.path))
  score = (
    0.5 * progress_score
    + 0.35 * distance_score
    + 0.25 * coverage
    + 0.15 * path_efficiency
  )
  if result.solved:
    score += 35.0 - 0.02 * len(result.path)
  return score


def _crossover(parent_a: Chromosome, parent_b: Chromosome, rng: Random) -> Chromosome:
  if not parent_a or not parent_b:
    return parent_a[:] if parent_a else parent_b[:]
  index_map_b: Dict[Cell, int] = {cell: idx for idx, cell in enumerate(parent_b)}
  shared = [cell for cell in parent_a if cell in index_map_b]
  if not shared:
    return parent_a[:] if rng.random() < 0.5 else parent_b[:]
  anchor = rng.choice(shared)
  idx_a = parent_a.index(anchor)
  idx_b = index_map_b[anchor]
  child = parent_a[: idx_a + 1] + parent_b[idx_b + 1 :]
  return simplify_path(child)


def _mutate(
  path: Chromosome,
  rng: Random,
  adjacency: Dict[Cell, List[Cell]],
  distance_map: List[List[int]],
  goal: Cell,
  max_steps: int,
  rate: float,
) -> Chromosome:
  if len(path) <= 1 or rng.random() > rate:
    return path[:]
  pivot = rng.randrange(len(path))
  trimmed = path[: pivot + 1]
  current = trimmed[-1]
  for _ in range(max_steps):
    if current == goal:
      break
    next_cell = biased_step(rng, current, adjacency, distance_map)
    if next_cell is None:
      break
    current = next_cell
    trimmed.append(current)
  return simplify_path(trimmed)


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
  mutation_rate: float = 0.05,
  capture_history: bool = False,
  seed: int | None = None,
) -> Dict[str, object]:
  """Run the genetic solver and optionally capture per-generation snapshots."""
  if not maze or not maze[0]:
    raise ValueError("maze must contain at least one row and column")
  if population_size <= 0:
    raise ValueError("population_size must be positive")
  if generations <= 0:
    raise ValueError("generations must be positive")
  if not 0 <= mutation_rate <= 1:
    raise ValueError("mutation_rate must be between 0 and 1")

  rng = Random(seed)
  start, goal = find_start_goal(maze)
  rows = len(maze)
  cols = len(maze[0])
  max_steps = max(rows * cols // 2, rows + cols)
  distance_map = build_distance_map(maze, goal)
  adjacency = build_adjacency(maze)

  population: List[Chromosome] = []
  if population_size > 1:
    population.extend(
      random_path(rng, start, goal, adjacency, distance_map, max_steps)
      for _ in range(population_size - 1)
    )
  population.append(greedy_path_to_goal(start, goal, adjacency, distance_map))
  best_overall: Individual | None = None
  frames: List[dict] = []
  last_population: List[Individual] = []

  for generation in range(generations):
    evaluated: List[Individual] = []
    for index, genes in enumerate(population):
      simulation = _evaluate_path(genes, goal, distance_map)
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

    last_population = evaluated
    evaluated.sort(key=lambda individual: individual.fitness, reverse=True)
    if best_overall is None or evaluated[0].fitness > best_overall.fitness:
      best_overall = evaluated[0]

    if capture_history:
      population_snapshot = _snapshot_population(evaluated, rng)
      frames.append(
        {
          "step": generation,
          "candidates": population_snapshot,
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
      child = _mutate(child, rng, adjacency, distance_map, goal, max_steps, mutation_rate)
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
    result["history"] = frames
  result["final_candidates"] = _snapshot_population(last_population, rng) if last_population else []
  result["best_candidate"] = {
    "index": best_overall.index,
    "path": _serialize_path(best_overall.path),
    "fitness": best_overall.fitness,
    "solved": best_overall.solved,
  }
  return result
