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

export const drawMaze = ({
  canvas,
  maze,
  explorers,
  bestPath,
  solution,
  frameProgress,
  isRunning,
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

  maze.forEach((row, rIdx) => {
    row.forEach((cell, cIdx) => {
      ctx.fillStyle = cell === 1 ? '#1e293b' : '#c3d3ebff';
      ctx.fillRect(cIdx * CELL_SIZE, rIdx * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    });
  });

  ctx.strokeStyle = '#334155';
  ctx.strokeRect(0, 0, canvas.width, canvas.height);

  const progress = isRunning ? frameProgress : 1;
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
  }

  if (bestPath && bestPath.length > 0) {
    drawPath(ctx, bestPath, '#ff0000ff', CELL_SIZE / 2.5, progress, 1);
  }

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
};

export { CELL_SIZE };
