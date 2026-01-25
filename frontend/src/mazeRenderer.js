const CELL_SIZE = 24;

const drawPath = (ctx, pathPoints, color, width, progress, alpha = 1) => {
  if (!pathPoints || pathPoints.length === 0) {
    return;
  }
  const visibleCount = Math.max(1, Math.floor(pathPoints.length * progress));
  const segment = pathPoints.slice(0, visibleCount);
  ctx.strokeStyle = color;
  ctx.globalAlpha = alpha;
  ctx.lineWidth = width;
  ctx.lineCap = 'round';
  ctx.beginPath();
  segment.forEach(([row, col], index) => {
    const x = col * CELL_SIZE + CELL_SIZE / 2;
    const y = row * CELL_SIZE + CELL_SIZE / 2;
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();
  ctx.globalAlpha = 1;
};

// Draw velocity vectors for PSO particles
const drawVelocityVectors = (ctx, explorers, progress) => {
  explorers.forEach((explorer) => {
    if (!explorer.velocity || explorer.path.length === 0) return;

    const visibleCount = Math.max(1, Math.floor(explorer.path.length * progress));
    const currentPos = explorer.path[Math.min(visibleCount - 1, explorer.path.length - 1)];

    if (!currentPos) return;

    const [row, col] = currentPos;
    const x = col * CELL_SIZE + CELL_SIZE / 2;
    const y = row * CELL_SIZE + CELL_SIZE / 2;

    const [vx, vy] = explorer.velocity;
    const magnitude = Math.sqrt(vx * vx + vy * vy);
    const scale = CELL_SIZE * 2;

    if (magnitude > 0.01) {
      ctx.strokeStyle = '#fbbf24';
      ctx.fillStyle = '#fbbf24';
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.7;

      const endX = x + (vx / magnitude) * scale * magnitude;
      const endY = y + (vy / magnitude) * scale * magnitude;

      // Draw arrow line
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(endX, endY);
      ctx.stroke();

      // Draw arrowhead
      const angle = Math.atan2(vy, vx);
      const arrowSize = 6;
      ctx.beginPath();
      ctx.moveTo(endX, endY);
      ctx.lineTo(
        endX - arrowSize * Math.cos(angle - Math.PI / 6),
        endY - arrowSize * Math.sin(angle - Math.PI / 6)
      );
      ctx.lineTo(
        endX - arrowSize * Math.cos(angle + Math.PI / 6),
        endY - arrowSize * Math.sin(angle + Math.PI / 6)
      );
      ctx.closePath();
      ctx.fill();

      ctx.globalAlpha = 1;
    }
  });
};

// Draw pheromone trails for Ant Colony Optimization
const drawPheromoneTrails = (ctx, pheromoneMap, rows, cols) => {
  if (!pheromoneMap) return;

  ctx.globalAlpha = 0.4;

  Object.entries(pheromoneMap).forEach(([key, strength]) => {
    const [row, col] = key.split(',').map(Number);

    // Color: Blue to cyan to green based on strength
    const hue = 180 + (strength * 60); // 180=cyan, 240=blue, 120=green
    const saturation = 70 + (strength * 30);
    const lightness = 40 + (strength * 30);

    ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    ctx.fillRect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE);

    // Draw stronger trails with glow
    if (strength > 0.5) {
      const gradient = ctx.createRadialGradient(
        col * CELL_SIZE + CELL_SIZE / 2,
        row * CELL_SIZE + CELL_SIZE / 2,
        0,
        col * CELL_SIZE + CELL_SIZE / 2,
        row * CELL_SIZE + CELL_SIZE / 2,
        CELL_SIZE
      );
      gradient.addColorStop(0, `hsla(${hue}, ${saturation}%, ${lightness}%, ${strength * 0.6})`);
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.fillStyle = gradient;
      ctx.fillRect(
        col * CELL_SIZE - CELL_SIZE / 2,
        row * CELL_SIZE - CELL_SIZE / 2,
        CELL_SIZE * 2,
        CELL_SIZE * 2
      );
    }
  });

  ctx.globalAlpha = 1;
};

// Draw fitness heatmap overlay for genetic algorithm
const drawFitnessHeatmap = (ctx, explorers, rows, cols) => {
  const cellVisits = {};
  const maxVisits = {};

  explorers.forEach((explorer) => {
    const fitness = explorer.fitness || 0;
    explorer.path.forEach(([row, col]) => {
      const key = `${row},${col}`;
      cellVisits[key] = (cellVisits[key] || 0) + fitness;
      maxVisits[key] = Math.max(maxVisits[key] || 0, fitness);
    });
  });

  const maxFitness = Math.max(...Object.values(maxVisits), 1);

  ctx.globalAlpha = 0.3;
  Object.entries(cellVisits).forEach(([key, value]) => {
    const [row, col] = key.split(',').map(Number);
    const intensity = Math.min(value / maxFitness, 1);

    const hue = 120 - (intensity * 60); // Green to yellow to red
    ctx.fillStyle = `hsl(${hue}, 80%, 50%)`;
    ctx.fillRect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE);
  });
  ctx.globalAlpha = 1;
};

// Highlight best performers with glow effect
const drawBestPerformers = (ctx, explorers, topN = 5) => {
  const sorted = [...explorers].sort((a, b) => (b.fitness || 0) - (a.fitness || 0));
  const best = sorted.slice(0, topN);

  best.forEach((explorer, rank) => {
    if (!explorer.path || explorer.path.length === 0) return;

    const lastPos = explorer.path[explorer.path.length - 1];
    if (!lastPos) return;

    const [row, col] = lastPos;
    const x = col * CELL_SIZE + CELL_SIZE / 2;
    const y = row * CELL_SIZE + CELL_SIZE / 2;

    // Draw glow
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, CELL_SIZE * 1.5);
    gradient.addColorStop(0, `rgba(255, 215, 0, ${0.6 - rank * 0.1})`);
    gradient.addColorStop(1, 'rgba(255, 215, 0, 0)');

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(x, y, CELL_SIZE * 1.5, 0, Math.PI * 2);
    ctx.fill();

    // Draw rank badge
    ctx.fillStyle = '#fbbf24';
    ctx.strokeStyle = '#78350f';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x - CELL_SIZE / 3, y - CELL_SIZE / 3, CELL_SIZE / 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#78350f';
    ctx.font = 'bold 10px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText((rank + 1).toString(), x - CELL_SIZE / 3, y - CELL_SIZE / 3);
  });
};

// Draw diversity indicator for population
const drawDiversityIndicator = (ctx, explorers, canvasWidth) => {
  if (!explorers || explorers.length === 0) return;

  const uniquePositions = new Set();
  explorers.forEach((explorer) => {
    if (explorer.path && explorer.path.length > 0) {
      const last = explorer.path[explorer.path.length - 1];
      uniquePositions.add(`${last[0]},${last[1]}`);
    }
  });

  const diversity = uniquePositions.size / explorers.length;

  // Draw diversity bar at bottom
  const barHeight = 8;
  const barY = 5;

  ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
  ctx.fillRect(5, barY, canvasWidth - 10, barHeight);

  const hue = diversity * 120; // Red to green
  ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
  ctx.fillRect(5, barY, (canvasWidth - 10) * diversity, barHeight);

  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 1;
  ctx.strokeRect(5, barY, canvasWidth - 10, barHeight);

  ctx.fillStyle = '#f8fafc';
  ctx.font = 'bold 10px sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText(`Diversity: ${(diversity * 100).toFixed(0)}%`, 10, barY + barHeight + 10);
};

// Draw convergence indicator
const drawConvergenceIndicator = (ctx, explorers, bestPath, canvasWidth, canvasHeight) => {
  if (!explorers || explorers.length === 0 || !bestPath || bestPath.length === 0) return;

  // Count how many explorers are near the best path
  const tolerance = 3; // cells
  let nearBest = 0;

  explorers.forEach((explorer) => {
    if (!explorer.path || explorer.path.length === 0) return;

    const lastPos = explorer.path[explorer.path.length - 1];
    const isNear = bestPath.some(([br, bc]) => {
      return Math.abs(br - lastPos[0]) <= tolerance && Math.abs(bc - lastPos[1]) <= tolerance;
    });

    if (isNear) nearBest++;
  });

  const convergence = nearBest / explorers.length;

  // Draw at top right
  const barWidth = 120;
  const barHeight = 8;
  const barX = canvasWidth - barWidth - 10;
  const barY = 5;

  ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
  ctx.fillRect(barX, barY, barWidth, barHeight);

  const hue = 200; // Blue theme
  ctx.fillStyle = `hsla(${hue}, 70%, 50%, ${0.5 + convergence * 0.5})`;
  ctx.fillRect(barX, barY, barWidth * convergence, barHeight);

  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 1;
  ctx.strokeRect(barX, barY, barWidth, barHeight);

  ctx.fillStyle = '#f8fafc';
  ctx.font = 'bold 10px sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText(`Convergence: ${(convergence * 100).toFixed(0)}%`, canvasWidth - 10, barY + barHeight + 10);
};

export const drawMaze = ({
  canvas,
  maze,
  explorers,
  bestPath,
  solution,
  frameProgress,
  isRunning,
  algorithmType,
  showVelocities,
  showHeatmap,
  showTopPerformers,
  showMetrics,
  showPheromones,
  pheromoneMap,
}) => {
  if (!canvas || !maze || maze.length === 0) {
    return;
  }

  const rows = maze.length;
  const cols = maze[0].length;
  canvas.width = cols * CELL_SIZE;
  canvas.height = rows * CELL_SIZE;

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw base maze
  maze.forEach((row, rIdx) => {
    row.forEach((cell, cIdx) => {
      ctx.fillStyle = cell === 1 ? '#1e293b' : '#c3d3ebff';
      ctx.fillRect(cIdx * CELL_SIZE, rIdx * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    });
  });

  // Draw pheromone trails for ant colony (if enabled)
  if (showPheromones && algorithmType === 'ant' && pheromoneMap) {
    drawPheromoneTrails(ctx, pheromoneMap, rows, cols);
  }

  // Draw fitness heatmap for genetic algorithm (if enabled)
  if (showHeatmap && algorithmType === 'genetic' && explorers && explorers.length > 0) {
    drawFitnessHeatmap(ctx, explorers, rows, cols);
  }

  ctx.strokeStyle = '#334155';
  ctx.strokeRect(0, 0, canvas.width, canvas.height);

  const progress = isRunning ? frameProgress : 1;

  // Draw explorer paths
  if (explorers && explorers.length > 0) {
    explorers.forEach((explorer, index) => {
      const hue = Math.round((index / explorers.length) * 360);
      const color = `hsla(${hue}, 70%, 65%, 0.65)`;
      drawPath(ctx, explorer.path, color, CELL_SIZE / 3, progress, 0.8);
      const visibleCount = Math.max(1, Math.floor(explorer.path.length * progress));
      const last = explorer.path?.[Math.min(visibleCount - 1, explorer.path.length - 1)];
      if (last) {
        const [row, col] = last;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(
          col * CELL_SIZE + CELL_SIZE / 2,
          row * CELL_SIZE + CELL_SIZE / 2,
          CELL_SIZE / 6,
          0,
          Math.PI * 2,
        );
        ctx.fill();
      }
    });

    // Draw velocity vectors for PSO (if enabled)
    if (showVelocities && algorithmType === 'pso') {
      drawVelocityVectors(ctx, explorers, progress);
    }

    // Highlight top performers (if enabled)
    if (showTopPerformers) {
      drawBestPerformers(ctx, explorers, 5);
    }
  }

  // Draw best path
  if (bestPath && bestPath.length > 0) {
    drawPath(ctx, bestPath, '#ff0000ff', CELL_SIZE / 2.5, progress, 1);
  }

  // Draw start and goal
  const start = solution?.start;
  const goal = solution?.goal;
  if (start) {
    ctx.fillStyle = '#10b981';
    ctx.fillRect(start[1] * CELL_SIZE, start[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE);
  }
  if (goal) {
    ctx.fillStyle = '#ef4444';
    ctx.fillRect(goal[1] * CELL_SIZE, goal[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE);
  }

  // Draw XAI metrics overlay (if enabled)
  if (showMetrics && explorers && explorers.length > 0) {
    drawDiversityIndicator(ctx, explorers, canvas.width);
    if (bestPath && bestPath.length > 0) {
      drawConvergenceIndicator(ctx, explorers, bestPath, canvas.width, canvas.height);
    }
  }
};

export { CELL_SIZE };
