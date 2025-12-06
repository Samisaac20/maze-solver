from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
  maze = generate_maze(size, seed=seed)
  return {
    "size": size,
    "seed": seed,
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
