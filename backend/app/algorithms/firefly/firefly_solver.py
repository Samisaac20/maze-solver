"""Firefly Algorithm maze solver with attraction-based movement and XAI features."""

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

MOVES_PER_ITERATION = 2


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
  """Build BFS distance map from goal."""
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


def _euclidean_distance(cell1: Cell, cell2: Cell) -> float:
  """Calculate Euclidean distance between two cells."""
  return ((cell1[0] - cell2[0])**2 + (cell1[1] - cell2[1])**2)**0.5


def _calculate_brightness(
  cell: Cell,
  goal: Cell,
  path_length: int,
  distance_map: List[List[int]],
) -> float:
  """
  Calculate firefly brightness based on position quality.
  Higher brightness = better position (closer to goal).
  """
  distance_to_goal = distance_map[cell[0]][cell[1]]
  
  # Base brightness from goal proximity (0-1 scale)
  max_distance = len(distance_map) + len(distance_map[0])
  if distance_to_goal >= 10**8:
    base_brightness = 0.0
  else:
    base_brightness = 1.0 - min(distance_to_goal / max_distance, 1.0)
  
  # Efficiency bonus (shorter paths = brighter)
  efficiency_factor = 1.0 / (1.0 + path_length * 0.001)
  
  # Goal bonus
  goal_bonus = 10.0 if cell == goal else 0.0
  
  brightness = base_brightness * efficiency_factor + goal_bonus
  return max(0.0, brightness)


def _get_valid_neighbors(
  current: Cell,
  maze: Grid,
  distance_map: List[List[int]],
) -> List[Cell]:
  """Get valid neighboring cells that can be moved to."""
  rows = len(maze)
  cols = len(maze[0])
  neighbors = []
  
  for dr, dc in DIRECTIONS:
    nr, nc = current[0] + dr, current[1] + dc
    if _in_bounds((nr, nc), rows, cols) and maze[nr][nc] == 0:
      neighbors.append((nr, nc))
  
  return neighbors


def _move_toward_attractor(
  current: Cell,
  attractor: Cell,
  maze: Grid,
  distance_map: List[List[int]],
  rng: Random,
  randomness: float,
) -> Cell:
  """
  Move current firefly toward a brighter firefly (attractor).
  Includes randomness for exploration.
  """
  neighbors = _get_valid_neighbors(current, maze, distance_map)
  
  if not neighbors:
    return current
  
  # If very close to attractor, might move randomly
  if rng.random() < randomness:
    return rng.choice(neighbors)
  
  # Calculate which neighbor is closest to attractor
  best_neighbor = current
  best_distance = _euclidean_distance(current, attractor)
  
  for neighbor in neighbors:
    dist = _euclidean_distance(neighbor, attractor)
    if dist < best_distance:
      best_distance = dist
      best_neighbor = neighbor
  
  return best_neighbor


def _serialize_path(path: Path) -> List[List[int]]:
  """Convert path to serializable format."""
  return [[row, col] for row, col in path]


@dataclass
class Firefly:
  """Represents a single firefly in the swarm."""
  cell: Cell
  trace: Path
  visited: Dict[Cell, int]
  brightness: float
  best_cell: Cell
  best_brightness: float
  best_trace: Path
  solved: bool = False


def solve_maze_with_firefly(
  maze: Grid,
  *,
  fireflies: int = 60,
  absorption: float = 1.0,
  iterations: int = 200,
  randomness: float = 0.2,
  seed: int | None = None,
  capture_history: bool = False,
) -> Dict[str, object]:
  """
  Solve maze using Firefly Algorithm with XAI features.
  
  Args:
    maze: 2D grid where 0=path, 1=wall
    fireflies: Number of fireflies in swarm
    absorption: Light absorption coefficient (higher = shorter attraction range)
    iterations: Number of iterations to run
    randomness: Probability of random movement (exploration)
    seed: Random seed for reproducibility
    capture_history: Whether to capture iteration history for visualization
  
  Returns:
    Dictionary containing solution and XAI data
  """
  if iterations <= 0:
    raise ValueError("iterations must be positive")
  if fireflies <= 0:
    raise ValueError("fireflies must be positive")
  if not 0 <= absorption <= 10:
    raise ValueError("absorption must be between 0 and 10")
  if not 0 <= randomness <= 1:
    raise ValueError("randomness must be between 0 and 1")
  if not maze or not maze[0]:
    raise ValueError("maze must contain at least one row and column")

  rng = Random(seed)
  start, goal = _find_start_goal(maze)
  distance_map = _build_distance_map(maze, goal)
  rows = len(maze)
  cols = len(maze[0])

  # Initialize firefly swarm at start
  swarm: List[Firefly] = []
  for _ in range(fireflies):
    initial_brightness = _calculate_brightness(start, goal, 1, distance_map)
    firefly = Firefly(
      cell=start,
      trace=[start],
      visited={start: 1},
      brightness=initial_brightness,
      best_cell=start,
      best_brightness=initial_brightness,
      best_trace=[start],
    )
    swarm.append(firefly)

  history: List[dict] = []
  best_overall: Firefly | None = None

  for iteration in range(iterations):
    # Sort fireflies by brightness (brightest first)
    swarm.sort(key=lambda f: f.brightness, reverse=True)
    
    # Update each firefly
    for i, firefly_i in enumerate(swarm):
      # Check brighter fireflies for attraction
      attracted = False
      
      for j in range(i):
        firefly_j = swarm[j]
        
        # Skip if j is not brighter
        if firefly_j.brightness <= firefly_i.brightness:
          continue
        
        # Calculate distance between fireflies
        distance = _euclidean_distance(firefly_i.cell, firefly_j.cell)
        
        # Calculate effective brightness with absorption
        # I(d) = I0 * e^(-γ * d²)
        import math
        effective_brightness = firefly_j.brightness * math.exp(-absorption * distance * distance / 100.0)
        
        # If brighter firefly is attractive, move toward it
        if effective_brightness > firefly_i.brightness:
          for _ in range(MOVES_PER_ITERATION):
            next_cell = _move_toward_attractor(
              firefly_i.cell,
              firefly_j.cell,
              maze,
              distance_map,
              rng,
              randomness,
            )
            
            if next_cell != firefly_i.cell:
              firefly_i.cell = next_cell
              firefly_i.trace.append(next_cell)
              
              # Trim trace if too long
              if len(firefly_i.trace) > rows * cols:
                firefly_i.trace = firefly_i.trace[-rows * cols:]
              
              firefly_i.visited[next_cell] = firefly_i.visited.get(next_cell, 0) + 1
            
            if next_cell == goal:
              firefly_i.solved = True
              break
          
          attracted = True
          break
      
      # If not attracted, move randomly with bias toward goal
      if not attracted:
        for _ in range(MOVES_PER_ITERATION):
          neighbors = _get_valid_neighbors(firefly_i.cell, maze, distance_map)
          if not neighbors:
            break
          
          # Bias toward goal with some randomness
          if rng.random() < 0.7:
            # Move toward goal
            neighbors.sort(key=lambda n: distance_map[n[0]][n[1]])
            next_cell = neighbors[0]
          else:
            # Random exploration
            next_cell = rng.choice(neighbors)
          
          if next_cell != firefly_i.cell:
            firefly_i.cell = next_cell
            firefly_i.trace.append(next_cell)
            
            if len(firefly_i.trace) > rows * cols:
              firefly_i.trace = firefly_i.trace[-rows * cols:]
            
            firefly_i.visited[next_cell] = firefly_i.visited.get(next_cell, 0) + 1
          
          if next_cell == goal:
            firefly_i.solved = True
            break
      
      # Update brightness based on new position
      firefly_i.brightness = _calculate_brightness(
        firefly_i.cell,
        goal,
        len(firefly_i.trace),
        distance_map,
      )
      
      # Update personal best
      if firefly_i.brightness > firefly_i.best_brightness:
        firefly_i.best_brightness = firefly_i.brightness
        firefly_i.best_cell = firefly_i.cell
        firefly_i.best_trace = firefly_i.trace.copy()
    
    # Track global best
    brightest = max(swarm, key=lambda f: f.best_brightness)
    if best_overall is None or brightest.best_brightness > best_overall.best_brightness:
      best_overall = brightest
    
    # Capture history for XAI
    if capture_history:
      iteration_candidates = [
        {
          "index": idx,
          "path": _serialize_path(ff.trace),
          "fitness": ff.brightness,
          "solved": ff.solved,
          "brightness": ff.brightness,  # XAI: brightness level
          "best_brightness": ff.best_brightness,  # XAI: personal best
        }
        for idx, ff in enumerate(swarm)
      ]
      
      history.append({
        "step": iteration,
        "candidates": iteration_candidates,
        "best": {
          "path": _serialize_path(brightest.best_trace),
          "fitness": brightest.best_brightness,
          "solved": brightest.solved,
          "brightness": brightest.best_brightness,
        },
      })
    
    # Check if solved
    if best_overall and best_overall.solved:
      break

  # Prepare result
  assert best_overall is not None
  
  result = {
    "solver": "firefly_algorithm",
    "solved": best_overall.solved,
    "start": start,
    "goal": goal,
    "fireflies": fireflies,
    "absorption": absorption,
    "iterations": iterations,
    "randomness": randomness,
    "best_fitness": best_overall.best_brightness,
    "path": _serialize_path(best_overall.best_trace),
  }
  
  if capture_history:
    result["history"] = history
  
  # Final candidates
  final_candidates = [
    {
      "index": idx,
      "path": _serialize_path(ff.trace),
      "fitness": ff.brightness,
      "solved": ff.solved,
      "brightness": ff.brightness,
      "best_brightness": ff.best_brightness,
    }
    for idx, ff in enumerate(swarm)
  ]
  result["final_candidates"] = final_candidates
  
  result["best_candidate"] = {
    "index": 0,  # After sorting, brightest is first
    "path": _serialize_path(best_overall.best_trace),
    "fitness": best_overall.best_brightness,
    "solved": best_overall.solved,
    "brightness": best_overall.best_brightness,
  }
  
  return result
