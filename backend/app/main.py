from random import randint

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .algorithms.ant_colony import solve_maze_with_ant_colony
from .algorithms.firefly import solve_maze_with_firefly
from .algorithms.genetic import solve_maze_with_genetic
from .algorithms.pso import solve_maze_with_pso
from .maze_logic.maze_gen import generate_maze, maze_to_string

DEFAULT_SIZE = 15
PSO_DEFAULTS = {"iterations": 240, "swarm_size": 70}
GENETIC_DEFAULTS = {"population_size": 80, "generations": 120, "mutation_rate": 0.05}
FIREFLY_DEFAULTS = {"fireflies": 60, "absorption": 1.0}
ANT_DEFAULTS = {"ants": 60, "evaporation_rate": 0.5}


def _resolved_seed(value: int | None) -> int:
  return value if value is not None else randint(0, 2**31 - 1)


def _build_maze(size: int, seed: int | None) -> tuple[list[list[int]], int]:
  actual_seed = _resolved_seed(seed)
  return generate_maze(size, seed=actual_seed), actual_seed


def _standard_payload(maze: list[list[int]], *, size: int, seed: int | None, extra: dict | None = None):
  payload = {
    "maze": maze,
    "size": size,
    "maze_seed": seed,
  }
  if extra:
    payload.update(extra)
  return payload


app = FastAPI(title="Maze Solver API", version="0.1.0")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.get("/health")
def health_check():
  return {"status": "ok"}


@app.get("/visuals/maze")
def visualize_maze(size: int = DEFAULT_SIZE, seed: int | None = None):
  maze, actual_seed = _build_maze(size, seed)
  return {
    "size": size,
    "seed": actual_seed,
    "grid": maze,
    "text": maze_to_string(maze),
  }


@app.get("/visuals/pso")
def visualize_pso(
  size: int = DEFAULT_SIZE,
  maze_seed: int | None = None,
  solver_seed: int | None = None,
  iterations: int = PSO_DEFAULTS["iterations"],
  swarm_size: int = PSO_DEFAULTS["swarm_size"],
):
  maze, resolved_seed = _build_maze(size, maze_seed)
  solution = solve_maze_with_pso(
    maze,
    iterations=iterations,
    swarm_size=swarm_size,
    seed=solver_seed,
    capture_history=True,
  )
  return _standard_payload(
    maze,
    size=size,
    seed=resolved_seed,
    extra={
      "solver_seed": solver_seed,
      "iterations": iterations,
      "swarm_size": swarm_size,
      "solution": solution,
    },
  )


@app.get("/visuals/genetic")
def visualize_genetic(
  size: int = DEFAULT_SIZE,
  maze_seed: int | None = None,
  population_size: int = GENETIC_DEFAULTS["population_size"],
  generations: int = GENETIC_DEFAULTS["generations"],
  mutation_rate: float = GENETIC_DEFAULTS["mutation_rate"],
):
  maze, resolved_seed = _build_maze(size, maze_seed)
  solution = solve_maze_with_genetic(
    maze,
    population_size=population_size,
    generations=generations,
    mutation_rate=mutation_rate,
    capture_history=True,
  )
  return _standard_payload(
    maze,
    size=size,
    seed=resolved_seed,
    extra={
      "population_size": population_size,
      "generations": generations,
      "mutation_rate": mutation_rate,
      "solution": solution,
    },
  )


@app.get("/visuals/firefly")
def visualize_firefly(
  size: int = DEFAULT_SIZE,
  maze_seed: int | None = None,
  fireflies: int = FIREFLY_DEFAULTS["fireflies"],
  absorption: float = FIREFLY_DEFAULTS["absorption"],
):
  maze, resolved_seed = _build_maze(size, maze_seed)
  solution = solve_maze_with_firefly(
    maze,
    fireflies=fireflies,
    absorption=absorption,
    capture_history=True,
  )
  return _standard_payload(
    maze,
    size=size,
    seed=resolved_seed,
    extra={
      "fireflies": fireflies,
      "absorption": absorption,
      "solution": solution,
    },
  )


@app.get("/visuals/ant-colony")
def visualize_ant_colony(
  size: int = DEFAULT_SIZE,
  maze_seed: int | None = None,
  ants: int = ANT_DEFAULTS["ants"],
  evaporation_rate: float = ANT_DEFAULTS["evaporation_rate"],
):
  maze, resolved_seed = _build_maze(size, maze_seed)
  solution = solve_maze_with_ant_colony(
    maze,
    ants=ants,
    evaporation_rate=evaporation_rate,
    capture_history=True,
  )
  return _standard_payload(
    maze,
    size=size,
    seed=resolved_seed,
    extra={
      "ants": ants,
      "evaporation_rate": evaporation_rate,
      "solution": solution,
    },
  )
