"""Enhanced maze generator with comprehensive complexity controls."""

from __future__ import annotations

from random import Random
from typing import Iterable, List, Sequence, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]

MAZE_SIZE = 30


def _neighbors(cell: Cell) -> Iterable[Cell]:
    """Get cells 2 steps away (for maze generation)."""
    row, col = cell
    for dr, dc in ((0, 2), (0, -2), (2, 0), (-2, 0)):
        yield row + dr, col + dc


def _in_bounds(cell: Cell, max_row: int, max_col: int) -> bool:
    """Check if cell is within maze boundaries."""
    row, col = cell
    return 1 <= row < max_row - 1 and 1 <= col < max_col - 1


def _get_wall_between(cell1: Cell, cell2: Cell) -> Cell:
    """Get the wall cell between two cells."""
    return (
        (cell1[0] + cell2[0]) // 2,
        (cell1[1] + cell2[1]) // 2,
    )


def _count_open_neighbors(cell: Cell, grid: Grid) -> int:
    """Count orthogonally adjacent open cells."""
    r, c = cell
    count = 0
    for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]):
            if grid[nr][nc] == 0:
                count += 1
    return count


def _get_removable_walls(grid: Grid, grid_span: int, rng: Random) -> List[Tuple[Cell, int]]:
    """
    Find walls that can be removed to create loops without creating artifacts.
    Returns list of (wall_cell, priority) tuples.
    """
    walls = []
    
    # Check horizontal walls (between vertically adjacent cells)
    for r in range(1, grid_span - 1, 2):
        for c in range(2, grid_span - 1, 2):
            if grid[r][c] == 1:  # Wall exists
                # Check if cells on both sides are open
                if grid[r][c - 1] == 0 and grid[r][c + 1] == 0:
                    # Priority: prefer walls near center
                    center_r, center_c = grid_span // 2, grid_span // 2
                    dist_from_center = abs(r - center_r) + abs(c - center_c)
                    priority = 100 - dist_from_center + rng.randint(-10, 10)
                    walls.append(((r, c), priority))
    
    # Check vertical walls (between horizontally adjacent cells)
    for r in range(2, grid_span - 1, 2):
        for c in range(1, grid_span - 1, 2):
            if grid[r][c] == 1:  # Wall exists
                # Check if cells above and below are open
                if grid[r - 1][c] == 0 and grid[r + 1][c] == 0:
                    center_r, center_c = grid_span // 2, grid_span // 2
                    dist_from_center = abs(r - center_r) + abs(c - center_c)
                    priority = 100 - dist_from_center + rng.randint(-10, 10)
                    walls.append(((r, c), priority))
    
    return walls


def _would_create_isolated_wall(wall: Cell, grid: Grid) -> bool:
    """Check if removing this wall would create an isolated wall cell."""
    rows, cols = len(grid), len(grid[0])
    r, c = wall
    
    # Check adjacent wall cells
    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
            # Count how many open neighbors this wall would have if we remove 'wall'
            open_count = 0
            for dr2, dc2 in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr2, nc2 = nr + dr2, nc + dc2
                if 0 <= nr2 < rows and 0 <= nc2 < cols:
                    if (nr2, nc2) == (r, c) or grid[nr2][nc2] == 0:
                        open_count += 1
            
            # A wall with 3+ open neighbors is isolated
            if open_count >= 3:
                return True
    
    return False


def _create_strategic_loops(
    grid: Grid, 
    grid_span: int, 
    loop_density: float, 
    rng: Random
) -> None:
    """
    Add loops and alternate paths to make maze more challenging.
    
    Args:
        loop_density: 0.0-1.0, controls how many alternate paths to create
                     0.0 = perfect maze (one path)
                     0.5 = moderate branching
                     1.0 = many alternate paths
    """
    if loop_density <= 0:
        return
    
    # Get all removable walls with priorities
    removable_walls = _get_removable_walls(grid, grid_span, rng)
    
    if not removable_walls:
        return
    
    # Sort by priority (higher first)
    removable_walls.sort(key=lambda x: x[1], reverse=True)
    
    # Calculate how many walls to remove based on loop_density
    max_removals = int(len(removable_walls) * loop_density * 0.4)  # Cap at 40% of walls
    removals_done = 0
    
    # Remove walls strategically
    for wall, priority in removable_walls:
        if removals_done >= max_removals:
            break
        
        # Skip if would create isolated walls
        if _would_create_isolated_wall(wall, grid):
            continue
        
        # Remove the wall
        grid[wall[0]][wall[1]] = 0
        removals_done += 1


def _create_dead_ends(
    grid: Grid,
    grid_span: int,
    dead_end_factor: float,
    rng: Random
) -> None:
    """
    Add dead-end branches to increase complexity.
    
    Args:
        dead_end_factor: 0.0-1.0, controls number of dead-end branches
                        0.0 = no extra dead ends
                        0.5 = moderate dead ends
                        1.0 = maximum dead ends
    """
    if dead_end_factor <= 0:
        return
    
    # Find all open cells that could spawn dead ends
    potential_starts = []
    for r in range(1, grid_span - 1, 2):
        for c in range(1, grid_span - 1, 2):
            if grid[r][c] == 0:
                open_neighbors = _count_open_neighbors((r, c), grid)
                # Good starting points have 1-2 open neighbors
                if 1 <= open_neighbors <= 2:
                    potential_starts.append((r, c))
    
    if not potential_starts:
        return
    
    # Number of dead ends to create
    num_dead_ends = int(len(potential_starts) * dead_end_factor * 0.3)
    
    for _ in range(num_dead_ends):
        if not potential_starts:
            break
        
        # Pick random starting point
        start = potential_starts.pop(rng.randrange(len(potential_starts)))
        
        # Create a short dead-end branch
        current = start
        branch_length = rng.randint(2, 6)
        
        for _ in range(branch_length):
            # Find available neighbors (not yet open)
            available = []
            for neighbor in _neighbors(current):
                if _in_bounds(neighbor, grid_span, grid_span):
                    if grid[neighbor[0]][neighbor[1]] == 1:  # Wall
                        wall = _get_wall_between(current, neighbor)
                        if grid[wall[0]][wall[1]] == 1:  # Wall between exists
                            # Check if neighbor would create too many openings
                            if _count_open_neighbors(neighbor, grid) == 0:
                                available.append((neighbor, wall))
            
            if not available:
                break
            
            # Pick random direction
            next_cell, wall = available[rng.randrange(len(available))]
            
            # Carve the path
            grid[wall[0]][wall[1]] = 0
            grid[next_cell[0]][next_cell[1]] = 0
            current = next_cell


def _widen_corridors(
    grid: Grid,
    grid_span: int,
    width_variation: float,
    rng: Random
) -> None:
    """
    Selectively widen some corridors to add variety.
    
    Args:
        width_variation: 0.0-1.0, controls corridor width diversity
                        0.0 = all corridors uniform
                        0.5 = some wider areas
                        1.0 = maximum variation
    """
    if width_variation <= 0:
        return
    
    # Find narrow corridors (walls between two parallel passages)
    widenable_walls = []
    
    for r in range(2, grid_span - 2):
        for c in range(2, grid_span - 2):
            if grid[r][c] == 1:  # Wall
                # Check for vertical widening opportunity
                if (grid[r][c-1] == 0 and grid[r][c+1] == 0 and
                    grid[r-1][c] == 0 and grid[r+1][c] == 0):
                    widenable_walls.append((r, c))
    
    if not widenable_walls:
        return
    
    # Widen some corridors
    num_to_widen = int(len(widenable_walls) * width_variation * 0.2)
    walls_to_remove = rng.sample(widenable_walls, min(num_to_widen, len(widenable_walls)))
    
    for wall in walls_to_remove:
        grid[wall[0]][wall[1]] = 0


def _add_chambers(
    grid: Grid,
    grid_span: int,
    chamber_density: float,
    rng: Random
) -> None:
    """
    Add open chamber areas for strategic interest.
    
    Args:
        chamber_density: 0.0-1.0, controls number of open chambers
                        0.0 = no chambers
                        0.5 = some chambers
                        1.0 = many chambers
    """
    if chamber_density <= 0:
        return
    
    # Number of chambers to create
    num_chambers = int((grid_span // 10) * chamber_density)
    
    for _ in range(num_chambers):
        # Random chamber center (must be on valid cell position)
        center_r = rng.randrange(3, grid_span - 3)
        center_c = rng.randrange(3, grid_span - 3)
        
        # Adjust to be on cell grid
        if center_r % 2 == 0:
            center_r += 1
        if center_c % 2 == 0:
            center_c += 1
        
        # Chamber size (2x2 or 3x3)
        size = rng.choice([2, 3]) if chamber_density > 0.5 else 2
        
        # Clear the chamber area
        for dr in range(-size, size + 1):
            for dc in range(-size, size + 1):
                r, c = center_r + dr, center_c + dc
                if 1 <= r < grid_span - 1 and 1 <= c < grid_span - 1:
                    grid[r][c] = 0


def _count_junctions(grid: Grid) -> int:
    """Count cells with 3+ exits (decision points)."""
    junctions = 0
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] == 0:  # Open cell
                if _count_open_neighbors((r, c), grid) >= 3:
                    junctions += 1
    return junctions


def generate_maze(
    size: int = MAZE_SIZE,
    seed: int | None = None,
    complexity: float = 0.5,
    dead_end_factor: float = 0.3,
    loop_density: float = 0.3,
    width_variation: float = 0.2,
    chamber_density: float = 0.1,
) -> Grid:
    """
    Generate maze with comprehensive complexity controls.
    
    Args:
        size: Maze dimension parameter (must be ≥5 and divisible by 5)
        seed: Random seed for reproducibility
        complexity: MASTER CONTROL 0.0-1.0 (overrides other params if set)
                   0.0 = minimal (perfect maze, easy)
                   0.5 = balanced (recommended)
                   1.0 = maximal (very complex, hard)
        dead_end_factor: 0.0-1.0, number of dead-end branches
        loop_density: 0.0-1.0, number of alternate paths/loops
        width_variation: 0.0-1.0, corridor width diversity
        chamber_density: 0.0-1.0, number of open chambers
    
    Complexity presets (when using master complexity parameter):
        0.0-0.2: EASY - Perfect maze, no dead ends, single solution path
        0.2-0.4: MEDIUM - Some loops, few dead ends, multiple paths
        0.4-0.6: BALANCED - Good mix of all features
        0.6-0.8: HARD - Many dead ends, loops, complex navigation
        0.8-1.0: EXTREME - Maximum confusion, many misleading paths
    
    Returns:
        2D grid where 0 = open path, 1 = wall
    """
    if size < 5:
        raise ValueError("size must be at least 5")
    if size % 5 != 0:
        raise ValueError("size must be a multiple of 5 to keep width and height aligned")
    if not 0 <= complexity <= 1:
        raise ValueError("complexity must be between 0 and 1")

    rng = Random(seed)
    grid_span = size * 2 + 1
    grid: Grid = [[1 for _ in range(grid_span)] for _ in range(grid_span)]

    start = (1, 1)
    goal = (grid_span - 2, grid_span - 2)
    
    # ===== PHASE 1: Generate perfect maze (guarantees connectivity) =====
    grid[start[0]][start[1]] = 0
    grid[goal[0]][goal[1]] = 0

    stack: List[Cell] = [start]
    visited: set[Cell] = {start}

    while stack:
        current = stack[-1]
        available = [
            n for n in _neighbors(current)
            if _in_bounds(n, grid_span, grid_span) and n not in visited
        ]

        if not available:
            stack.pop()
            continue

        next_cell = rng.choice(available)
        wall = _get_wall_between(current, next_cell)

        grid[wall[0]][wall[1]] = 0
        grid[next_cell[0]][next_cell[1]] = 0
        visited.add(next_cell)
        stack.append(next_cell)

    # ===== PHASE 2: Apply complexity features =====
    # If complexity is set, derive individual parameters from it
    if complexity is not None:
        # Scale factors based on complexity
        dead_end_factor = complexity * 0.6  # More dead ends = harder
        loop_density = 0.1 + (complexity * 0.3)  # Some loops help, but not too many
        width_variation = complexity * 0.3
        chamber_density = max(0, complexity - 0.3) * 0.3  # Only at higher complexity
    
    # Add features in order of impact
    _create_strategic_loops(grid, grid_span, loop_density, rng)
    _create_dead_ends(grid, grid_span, dead_end_factor, rng)
    _widen_corridors(grid, grid_span, width_variation, rng)
    _add_chambers(grid, grid_span, chamber_density, rng)

    return grid


def maze_to_string(grid: Sequence[Sequence[int]]) -> str:
    """Turn maze cells into a simple text view for debugging."""
    return "\n".join("".join("#" if cell else " " for cell in row) for row in grid)


def analyze_maze_complexity(grid: Grid) -> dict:
    """Analyze maze complexity metrics."""
    open_cells = sum(1 for row in grid for cell in row if cell == 0)
    total_cells = len(grid) * len(grid[0])
    junctions = _count_junctions(grid)
    
    # Count dead ends (cells with only 1 exit)
    dead_ends = 0
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] == 0:
                if _count_open_neighbors((r, c), grid) == 1:
                    dead_ends += 1
    
    return {
        "open_cells": open_cells,
        "total_cells": total_cells,
        "openness": open_cells / total_cells,
        "junctions": junctions,
        "dead_ends": dead_ends,
        "decisions_per_100_cells": (junctions / open_cells * 100) if open_cells > 0 else 0,
        "dead_ends_per_100_cells": (dead_ends / open_cells * 100) if open_cells > 0 else 0,
    }


def get_complexity_preset(preset_name: str) -> dict:
    """
    Get predefined complexity settings.
    
    Presets:
        'trivial': Perfect maze, easiest possible
        'easy': Minimal complexity
        'medium': Balanced for learning
        'hard': Challenging navigation
        'extreme': Maximum confusion
        'algorithm_test': Optimized for testing algorithms
    """
    presets = {
        'trivial': {
            'complexity': 0.0,
            'dead_end_factor': 0.0,
            'loop_density': 0.0,
            'width_variation': 0.0,
            'chamber_density': 0.0,
        },
        'easy': {
            'complexity': 0.2,
            'dead_end_factor': 0.1,
            'loop_density': 0.15,
            'width_variation': 0.1,
            'chamber_density': 0.0,
        },
        'medium': {
            'complexity': 0.5,
            'dead_end_factor': 0.3,
            'loop_density': 0.25,
            'width_variation': 0.2,
            'chamber_density': 0.1,
        },
        'hard': {
            'complexity': 0.7,
            'dead_end_factor': 0.5,
            'loop_density': 0.35,
            'width_variation': 0.3,
            'chamber_density': 0.2,
        },
        'extreme': {
            'complexity': 0.95,
            'dead_end_factor': 0.7,
            'loop_density': 0.4,
            'width_variation': 0.4,
            'chamber_density': 0.3,
        },
        'algorithm_test': {
            'complexity': 0.4,
            'dead_end_factor': 0.4,  # Test dead-end handling
            'loop_density': 0.3,     # Test multiple path exploration
            'width_variation': 0.1,
            'chamber_density': 0.15, # Test open space navigation
        },
    }
    
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
    
    return presets[preset_name]


__all__ = [
    "generate_maze", 
    "maze_to_string", 
    "analyze_maze_complexity",
    "get_complexity_preset"
]
