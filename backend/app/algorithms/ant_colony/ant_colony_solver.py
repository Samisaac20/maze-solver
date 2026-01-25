"""Ant Colony Optimization maze solver with pheromone trails and XAI features."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from random import Random
from typing import Dict, List, Sequence, Tuple

Grid = Sequence[Sequence[int]]
Cell = Tuple[int, int]
Path = List[Cell]

DIRECTIONS: Tuple[Cell, ...] = (
  (0, 1),   # Right
  (1, 0),   # Down
  (0, -1),  # Left
  (-1, 0),  # Up
)


def _find_start_goal(maze: Grid) -> Tuple[Cell, Cell]:
  """Find the start (top-left) and goal (bottom-right) open cells."""
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
    raise ValueError("maze must have at least one open cell for start/goal")
  return start, goal


def _in_bounds(cell: Cell, rows: int, cols: int) -> bool:
  """Check if cell is within maze boundaries."""
  return 0 <= cell[0] < rows and 0 <= cell[1] < cols


def _build_distance_map(maze: Grid, goal: Cell) -> List[List[int]]:
  """Build BFS distance map from goal (heuristic information)."""
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


def _get_valid_neighbors(
  current: Cell,
  maze: Grid,
  visited: set[Cell],
) -> List[Cell]:
  """Get valid neighboring cells that haven't been visited."""
  rows = len(maze)
  cols = len(maze[0])
  neighbors = []
  
  for dr, dc in DIRECTIONS:
    nr, nc = current[0] + dr, current[1] + dc
    if _in_bounds((nr, nc), rows, cols) and maze[nr][nc] == 0:
      if (nr, nc) not in visited:
        neighbors.append((nr, nc))
  
  return neighbors


def _select_next_cell(
  current: Cell,
  neighbors: List[Cell],
  pheromones: Dict[Tuple[Cell, Cell], float],
  distance_map: List[List[int]],
  alpha: float,
  beta: float,
  rng: Random,
) -> Cell | None:
  """
  Select next cell based on pheromone trails and heuristic information.
  
  Probability = (pheromone^alpha) * (heuristic^beta)
  
  Args:
    alpha: Pheromone importance (higher = follow trails more)
    beta: Heuristic importance (higher = follow goal direction more)
  """
  if not neighbors:
    return None
  
  # Calculate probabilities for each neighbor
  probabilities = []
  total = 0.0
  
  for neighbor in neighbors:
    edge = (current, neighbor)
    
    # Pheromone level
    tau = pheromones.get(edge, 0.1)  # Default small pheromone
    
    # Heuristic: inverse of distance to goal (closer = better)
    distance = distance_map[neighbor[0]][neighbor[1]]
    if distance >= 10**8:
      eta = 0.01  # Very small if unreachable
    else:
      eta = 1.0 / (1.0 + distance)
    
    # Combined probability
    prob = (tau ** alpha) * (eta ** beta)
    probabilities.append(prob)
    total += prob
  
  if total == 0:
    # All probabilities zero, choose randomly
    return rng.choice(neighbors)
  
  # Normalize probabilities
  probabilities = [p / total for p in probabilities]
  
  # Roulette wheel selection
  r = rng.random()
  cumulative = 0.0
  for i, prob in enumerate(probabilities):
    cumulative += prob
    if r <= cumulative:
      return neighbors[i]
  
  return neighbors[-1]  # Fallback


def _update_pheromones(
  pheromones: Dict[Tuple[Cell, Cell], float],
  ant_paths: List[Tuple[Path, bool]],
  evaporation_rate: float,
  goal: Cell,
  distance_map: List[List[int]],
) -> None:
  """
  Update pheromone trails based on ant paths.
  
  1. Evaporate existing pheromones
  2. Deposit new pheromones on paths taken
  """
  # Evaporation
  for edge in list(pheromones.keys()):
    pheromones[edge] *= (1.0 - evaporation_rate)
    if pheromones[edge] < 0.01:
      del pheromones[edge]
  
  # Deposit pheromones from successful ants
  for path, solved in ant_paths:
    if len(path) < 2:
      continue
    
    # Calculate pheromone deposit amount
    # Shorter paths deposit more pheromone
    path_length = len(path)
    
    # Bonus for reaching goal
    if solved:
      deposit = 10.0 / path_length
    else:
      # Partial credit based on how close they got
      final_cell = path[-1]
      final_distance = distance_map[final_cell[0]][final_cell[1]]
      start_distance = distance_map[path[0][0]][path[0][1]]
      
      if start_distance > 0:
        progress = max(0, (start_distance - final_distance) / start_distance)
        deposit = progress / path_length
      else:
        deposit = 0.1 / path_length
    
    # Deposit on each edge in path
    for i in range(len(path) - 1):
      edge = (path[i], path[i + 1])
      pheromones[edge] = pheromones.get(edge, 0.0) + deposit


def _serialize_path(path: Path) -> List[List[int]]:
  """Convert path to serializable format."""
  return [[row, col] for row, col in path]


@dataclass
class Ant:
  """Represents a single ant."""
  current: Cell
  path: Path
  visited: set[Cell]
  solved: bool = False


def solve_maze_with_ant_colony(
  maze: Grid,
  *,
  ants: int = 60,
  iterations: int = 150,
  evaporation_rate: float = 0.5,
  alpha: float = 1.0,
  beta: float = 2.0,
  seed: int | None = None,
  capture_history: bool = False,
) -> Dict[str, object]:
  """
  Solve maze using Ant Colony Optimization with XAI features.
  
  Args:
    maze: 2D grid where 0=path, 1=wall
    ants: Number of ants per iteration
    iterations: Number of iterations to run
    evaporation_rate: Pheromone evaporation rate (0-1)
    alpha: Pheromone importance weight
    beta: Heuristic importance weight
    seed: Random seed for reproducibility
    capture_history: Whether to capture iteration history
  
  Returns:
    Dictionary containing solution and XAI data including pheromone trails
  """
  if iterations <= 0:
    raise ValueError("iterations must be positive")
  if ants <= 0:
    raise ValueError("ants must be positive")
  if not 0 <= evaporation_rate <= 1:
    raise ValueError("evaporation_rate must be between 0 and 1")
  if not maze or not maze[0]:
    raise ValueError("maze must contain at least one row and column")

  rng = Random(seed)
  start, goal = _find_start_goal(maze)
  distance_map = _build_distance_map(maze, goal)
  rows = len(maze)
  cols = len(maze[0])
  max_steps = rows * cols

  # Pheromone trails: edge -> pheromone level
  pheromones: Dict[Tuple[Cell, Cell], float] = {}
  
  best_path: Path | None = None
  best_path_length = float('inf')
  history: List[dict] = []

  for iteration in range(iterations):
    # Deploy ants
    ant_colony: List[Ant] = []
    for _ in range(ants):
      ant = Ant(
        current=start,
        path=[start],
        visited={start},
      )
      ant_colony.append(ant)
    
    # Let each ant explore
    for ant in ant_colony:
      for _ in range(max_steps):
        if ant.current == goal:
          ant.solved = True
          break
        
        # Get valid unvisited neighbors
        neighbors = _get_valid_neighbors(ant.current, maze, ant.visited)
        
        if not neighbors:
          # Dead end, ant stops
          break
        
        # Select next cell based on pheromones and heuristic
        next_cell = _select_next_cell(
          ant.current,
          neighbors,
          pheromones,
          distance_map,
          alpha,
          beta,
          rng,
        )
        
        if next_cell is None:
          break
        
        # Move ant
        ant.current = next_cell
        ant.path.append(next_cell)
        ant.visited.add(next_cell)
    
    # Collect paths for pheromone update
    ant_paths = [(ant.path, ant.solved) for ant in ant_colony]
    
    # Update pheromones
    _update_pheromones(
      pheromones,
      ant_paths,
      evaporation_rate,
      goal,
      distance_map,
    )
    
    # Track best solution
    for ant in ant_colony:
      if ant.solved and len(ant.path) < best_path_length:
        best_path = ant.path.copy()
        best_path_length = len(ant.path)
    
    # Capture history for XAI
    if capture_history:
      # Calculate pheromone strength for each cell (for visualization)
      cell_pheromones: Dict[Cell, float] = {}
      for (cell1, cell2), strength in pheromones.items():
        cell_pheromones[cell1] = max(cell_pheromones.get(cell1, 0), strength)
        cell_pheromones[cell2] = max(cell_pheromones.get(cell2, 0), strength)
      
      iteration_candidates = [
        {
          "index": idx,
          "path": _serialize_path(ant.path),
          "fitness": len(ant.path) if ant.solved else 0,
          "solved": ant.solved,
          "pheromone_strength": cell_pheromones.get(ant.path[-1], 0.0) if ant.path else 0.0,
        }
        for idx, ant in enumerate(ant_colony)
      ]
      
      # Calculate overall pheromone map for visualization
      max_pheromone = max(pheromones.values()) if pheromones else 1.0
      pheromone_map = {}
      for cell, strength in cell_pheromones.items():
        pheromone_map[f"{cell[0]},{cell[1]}"] = strength / max_pheromone
      
      history.append({
        "step": iteration,
        "candidates": iteration_candidates,
        "best": {
          "path": _serialize_path(best_path) if best_path else [],
          "fitness": len(best_path) if best_path else 0,
          "solved": best_path is not None,
        },
        "pheromone_map": pheromone_map,  # XAI: pheromone trail strength
      })
    
    # Early termination if solution found and stable
    if best_path and iteration > 20:
      # Check if recent iterations haven't improved
      if iteration > 50:
        break

  # Prepare result
  result = {
    "solver": "ant_colony_optimization",
    "solved": best_path is not None,
    "start": start,
    "goal": goal,
    "ants": ants,
    "iterations": iterations,
    "evaporation_rate": evaporation_rate,
    "alpha": alpha,
    "beta": beta,
    "best_fitness": len(best_path) if best_path else 0,
    "path": _serialize_path(best_path) if best_path else [],
  }
  
  if capture_history:
    result["history"] = history
  
  # Calculate final pheromone strengths for cells
  cell_pheromones: Dict[Cell, float] = {}
  for (cell1, cell2), strength in pheromones.items():
    cell_pheromones[cell1] = max(cell_pheromones.get(cell1, 0), strength)
    cell_pheromones[cell2] = max(cell_pheromones.get(cell2, 0), strength)
  
  max_pheromone = max(cell_pheromones.values()) if cell_pheromones else 1.0
  
  # Final candidates (last iteration)
  if ant_colony:
    final_candidates = [
      {
        "index": idx,
        "path": _serialize_path(ant.path),
        "fitness": len(ant.path) if ant.solved else 0,
        "solved": ant.solved,
        "pheromone_strength": cell_pheromones.get(ant.path[-1], 0.0) / max_pheromone if ant.path else 0.0,
      }
      for idx, ant in enumerate(ant_colony)
    ]
    result["final_candidates"] = final_candidates
  
  result["best_candidate"] = {
    "index": 0,
    "path": _serialize_path(best_path) if best_path else [],
    "fitness": len(best_path) if best_path else 0,
    "solved": best_path is not None,
  }
  
  return result
