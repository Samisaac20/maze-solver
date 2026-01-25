from random import randint

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from algorithms.ant_colony import solve_maze_with_ant_colony
from algorithms.firefly import solve_maze_with_firefly
from algorithms.genetic import solve_maze_with_genetic
from algorithms.pso import solve_maze_with_pso
from maze_logic.maze_gen import generate_maze, maze_to_string, analyze_maze_complexity, get_complexity_preset

DEFAULT_SIZE = 15
PSO_DEFAULTS = {"iterations": 240, "swarm_size": 70}
GENETIC_DEFAULTS = {"population_size": 80, "generations": 120, "mutation_rate": 0.05}
FIREFLY_DEFAULTS = {"fireflies": 60, "absorption": 1.0}
ANT_DEFAULTS = {"ants": 60, "evaporation_rate": 0.5}

# Complexity defaults
COMPLEXITY_DEFAULTS = {
  "complexity": 0.5,
  "dead_end_factor": 0.3,
  "loop_density": 0.3,
  "width_variation": 0.2,
  "chamber_density": 0.1,
}


def _resolved_seed(value: int | None) -> int:
  return value if value is not None else randint(0, 2**31 - 1)


def _build_maze(
  size: int, 
  seed: int | None,
  complexity: float | None = None,
  dead_end_factor: float | None = None,
  loop_density: float | None = None,
  width_variation: float | None = None,
  chamber_density: float | None = None,
  preset: str | None = None,
) -> tuple[list[list[int]], int]:
  """Build maze with optional complexity controls."""
  actual_seed = _resolved_seed(seed)
  
  # If preset is specified, use those settings
  if preset:
    preset_settings = get_complexity_preset(preset)
    return generate_maze(size, seed=actual_seed, **preset_settings), actual_seed
  
  # Otherwise use provided parameters or defaults
  kwargs = {}
  if complexity is not None:
    kwargs['complexity'] = complexity
  if dead_end_factor is not None:
    kwargs['dead_end_factor'] = dead_end_factor
  if loop_density is not None:
    kwargs['loop_density'] = loop_density
  if width_variation is not None:
    kwargs['width_variation'] = width_variation
  if chamber_density is not None:
    kwargs['chamber_density'] = chamber_density
  
  # Apply defaults for unspecified parameters
  for key, default_value in COMPLEXITY_DEFAULTS.items():
    if key not in kwargs:
      kwargs[key] = default_value
  
  return generate_maze(size, seed=actual_seed, **kwargs), actual_seed


def _standard_payload(maze: list[list[int]], *, size: int, seed: int | None, extra: dict | None = None):
  payload = {
    "maze": maze,
    "size": size,
    "maze_seed": seed,
  }
  if extra:
    payload.update(extra)
  return payload


app = FastAPI(title="Maze Solver API", version="0.2.0")

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
def visualize_maze(
  size: int = DEFAULT_SIZE,
  seed: int | None = None,
  complexity: float | None = None,
  dead_end_factor: float | None = None,
  loop_density: float | None = None,
  width_variation: float | None = None,
  chamber_density: float | None = None,
  preset: str | None = None,
):
  """
  Generate a maze with complexity controls.
  
  Parameters:
    - size: Maze size (15, 20, 25, etc.)
    - seed: Random seed for reproducibility
    - complexity: Master complexity 0.0-1.0 (overrides individual params)
    - dead_end_factor: 0.0-1.0, number of dead-end branches
    - loop_density: 0.0-1.0, number of alternate paths
    - width_variation: 0.0-1.0, corridor width diversity
    - chamber_density: 0.0-1.0, number of open chambers
    - preset: Use preset ('trivial', 'easy', 'medium', 'hard', 'extreme', 'algorithm_test')
  """
  maze, actual_seed = _build_maze(
    size, seed, complexity, dead_end_factor, 
    loop_density, width_variation, chamber_density, preset
  )
  
  # Analyze the generated maze
  analysis = analyze_maze_complexity(maze)
  
  return {
    "size": size,
    "seed": actual_seed,
    "grid": maze,
    "text": maze_to_string(maze),
    "analysis": analysis,
    "complexity_settings": {
      "complexity": complexity,
      "dead_end_factor": dead_end_factor,
      "loop_density": loop_density,
      "width_variation": width_variation,
      "chamber_density": chamber_density,
      "preset": preset,
    }
  }


@app.get("/complexity/presets")
def get_complexity_presets():
  """Get available complexity presets."""
  return {
    "presets": {
      "trivial": {
        "description": "Perfect maze, easiest possible - single solution path",
        "difficulty": "★☆☆☆☆",
        "recommended_for": "Testing basic pathfinding",
      },
      "easy": {
        "description": "Minimal complexity - few dead ends, some alternate paths",
        "difficulty": "★★☆☆☆",
        "recommended_for": "Learning and debugging",
      },
      "medium": {
        "description": "Balanced complexity - good mix of features",
        "difficulty": "★★★☆☆",
        "recommended_for": "General algorithm testing",
      },
      "hard": {
        "description": "Challenging navigation - many dead ends and loops",
        "difficulty": "★★★★☆",
        "recommended_for": "Stress testing algorithms",
      },
      "extreme": {
        "description": "Maximum confusion - very complex maze",
        "difficulty": "★★★★★",
        "recommended_for": "Advanced algorithm comparison",
      },
      "algorithm_test": {
        "description": "Optimized for testing algorithm behavior",
        "difficulty": "★★★☆☆",
        "recommended_for": "XAI demonstrations and research",
      },
    }
  }


@app.get("/visuals/pso")
def visualize_pso(
  size: int = DEFAULT_SIZE,
  maze_seed: int | None = None,
  solver_seed: int | None = None,
  iterations: int = PSO_DEFAULTS["iterations"],
  swarm_size: int = PSO_DEFAULTS["swarm_size"],
  complexity: float | None = None,
  dead_end_factor: float | None = None,
  loop_density: float | None = None,
  width_variation: float | None = None,
  chamber_density: float | None = None,
  preset: str | None = None,
):
  maze, resolved_seed = _build_maze(
    size, maze_seed, complexity, dead_end_factor,
    loop_density, width_variation, chamber_density, preset
  )
  solution = solve_maze_with_pso(
    maze,
    iterations=iterations,
    swarm_size=swarm_size,
    seed=solver_seed,
    capture_history=True,
  )
  
  analysis = analyze_maze_complexity(maze)
  
  return _standard_payload(
    maze,
    size=size,
    seed=resolved_seed,
    extra={
      "solver_seed": solver_seed,
      "iterations": iterations,
      "swarm_size": swarm_size,
      "solution": solution,
      "maze_analysis": analysis,
    },
  )


@app.get("/visuals/genetic")
def visualize_genetic(
  size: int = DEFAULT_SIZE,
  maze_seed: int | None = None,
  population_size: int = GENETIC_DEFAULTS["population_size"],
  generations: int = GENETIC_DEFAULTS["generations"],
  mutation_rate: float = GENETIC_DEFAULTS["mutation_rate"],
  complexity: float | None = None,
  dead_end_factor: float | None = None,
  loop_density: float | None = None,
  width_variation: float | None = None,
  chamber_density: float | None = None,
  preset: str | None = None,
):
  maze, resolved_seed = _build_maze(
    size, maze_seed, complexity, dead_end_factor,
    loop_density, width_variation, chamber_density, preset
  )
  solution = solve_maze_with_genetic(
    maze,
    population_size=population_size,
    generations=generations,
    mutation_rate=mutation_rate,
    capture_history=True,
  )
  
  analysis = analyze_maze_complexity(maze)
  
  return _standard_payload(
    maze,
    size=size,
    seed=resolved_seed,
    extra={
      "population_size": population_size,
      "generations": generations,
      "mutation_rate": mutation_rate,
      "solution": solution,
      "maze_analysis": analysis,
    },
  )


@app.get("/visuals/firefly")
def visualize_firefly(
  size: int = DEFAULT_SIZE,
  maze_seed: int | None = None,
  fireflies: int = FIREFLY_DEFAULTS["fireflies"],
  absorption: float = FIREFLY_DEFAULTS["absorption"],
  iterations: int = 200,
  randomness: float = 0.2,
  complexity: float | None = None,
  dead_end_factor: float | None = None,
  loop_density: float | None = None,
  width_variation: float | None = None,
  chamber_density: float | None = None,
  preset: str | None = None,
):
  maze, resolved_seed = _build_maze(
    size, maze_seed, complexity, dead_end_factor,
    loop_density, width_variation, chamber_density, preset
  )
  solution = solve_maze_with_firefly(
    maze,
    fireflies=fireflies,
    absorption=absorption,
    iterations=iterations,
    randomness=randomness,
    capture_history=True,
  )
  
  analysis = analyze_maze_complexity(maze)
  
  return _standard_payload(
    maze,
    size=size,
    seed=resolved_seed,
    extra={
      "fireflies": fireflies,
      "absorption": absorption,
      "iterations": iterations,
      "randomness": randomness,
      "solution": solution,
      "maze_analysis": analysis,
    },
  )


@app.get("/visuals/ant-colony")
def visualize_ant_colony(
  size: int = DEFAULT_SIZE,
  maze_seed: int | None = None,
  ants: int = ANT_DEFAULTS["ants"],
  iterations: int = 150,
  evaporation_rate: float = ANT_DEFAULTS["evaporation_rate"],
  alpha: float = 1.0,
  beta: float = 2.0,
  complexity: float | None = None,
  dead_end_factor: float | None = None,
  loop_density: float | None = None,
  width_variation: float | None = None,
  chamber_density: float | None = None,
  preset: str | None = None,
):
  maze, resolved_seed = _build_maze(
    size, maze_seed, complexity, dead_end_factor,
    loop_density, width_variation, chamber_density, preset
  )
  solution = solve_maze_with_ant_colony(
    maze,
    ants=ants,
    iterations=iterations,
    evaporation_rate=evaporation_rate,
    alpha=alpha,
    beta=beta,
    capture_history=True,
  )
  
  analysis = analyze_maze_complexity(maze)
  
  return _standard_payload(
    maze,
    size=size,
    seed=resolved_seed,
    extra={
      "ants": ants,
      "iterations": iterations,
      "evaporation_rate": evaporation_rate,
      "alpha": alpha,
      "beta": beta,
      "solution": solution,
      "maze_analysis": analysis,
    },
  )
