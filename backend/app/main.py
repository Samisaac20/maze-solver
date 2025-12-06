from random import randint

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .algorithms.ant_colony import solve_maze_with_ant_colony
from .algorithms.firefly import solve_maze_with_firefly
from .algorithms.genetic import solve_maze_with_genetic
from .algorithms.pso import solve_maze_with_pso
from .maze_logic.maze_gen import generate_maze, maze_to_string

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
def visualize_maze(size: int = 6, seed: int | None = None):
  """Provide a freshly carved maze in matrix and text forms."""
  actual_seed = seed if seed is not None else randint(0, 2**31 - 1)
  maze = generate_maze(size, seed=actual_seed)
  return {
    "size": size,
    "seed": actual_seed,
    "grid": maze,
    "text": maze_to_string(maze),
  }


@app.get("/visuals/pso")
def visualize_pso(
  size: int = 6,
  maze_seed: int | None = None,
  solver_seed: int | None = None,
  iterations: int = 40,
  swarm_size: int = 12,
):
  """Run PSO on a generated maze and expose iteration history for the frontend."""
  maze = generate_maze(size, seed=maze_seed)
  solution = solve_maze_with_pso(
    maze,
    iterations=iterations,
    swarm_size=swarm_size,
    seed=solver_seed,
    capture_history=True,
  )
  return {
    "maze": maze,
    "size": size,
    "maze_seed": maze_seed,
    "solver_seed": solver_seed,
    "iterations": iterations,
    "swarm_size": swarm_size,
    "solution": solution,
  }


@app.get("/visuals/genetic")
def visualize_genetic(
  size: int = 6,
  maze_seed: int | None = None,
  population_size: int = 80,
  generations: int = 120,
):
  """Return placeholder data for the genetic algorithm solver."""
  maze = generate_maze(size, seed=maze_seed)
  solution = solve_maze_with_genetic(
    maze,
    population_size=population_size,
    generations=generations,
    capture_history=True,
  )
  return {
    "maze": maze,
    "size": size,
    "maze_seed": maze_seed,
    "population_size": population_size,
    "generations": generations,
    "solution": solution,
  }


@app.get("/visuals/firefly")
def visualize_firefly(
  size: int = 6,
  maze_seed: int | None = None,
  fireflies: int = 60,
  absorption: float = 1.0,
):
  """Return placeholder data for the Firefly algorithm solver."""
  maze = generate_maze(size, seed=maze_seed)
  solution = solve_maze_with_firefly(
    maze,
    fireflies=fireflies,
    absorption=absorption,
    capture_history=True,
  )
  return {
    "maze": maze,
    "size": size,
    "maze_seed": maze_seed,
    "fireflies": fireflies,
    "absorption": absorption,
    "solution": solution,
  }


@app.get("/visuals/ant-colony")
def visualize_ant_colony(
  size: int = 6,
  maze_seed: int | None = None,
  ants: int = 60,
  evaporation_rate: float = 0.5,
):
  """Return placeholder data for the Ant Colony Optimization solver."""
  maze = generate_maze(size, seed=maze_seed)
  solution = solve_maze_with_ant_colony(
    maze,
    ants=ants,
    evaporation_rate=evaporation_rate,
    capture_history=True,
  )
  return {
    "maze": maze,
    "size": size,
    "maze_seed": maze_seed,
    "ants": ants,
    "evaporation_rate": evaporation_rate,
    "solution": solution,
  }
