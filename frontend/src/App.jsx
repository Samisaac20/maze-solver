import { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const CELL_SIZE = 24;

function App() {
  const canvasRef = useRef(null);
  const [maze, setMaze] = useState([]);
  const [history, setHistory] = useState([]);
  const [solution, setSolution] = useState(null);
  const MIN_SIZE = 15;
  const MAX_SIZE = 100;

  const normalizeSize = (value) => {
    if (Number.isNaN(value)) {
      return MIN_SIZE;
    }
    let clamped = Math.max(MIN_SIZE, Math.min(MAX_SIZE, value));
    clamped = Math.round(clamped / 5) * 5;
    clamped = Math.max(MIN_SIZE, Math.min(MAX_SIZE, clamped));
    return clamped;
  };

  const [mazeSize, setMazeSize] = useState(null);
  const [mazeSeed, setMazeSeed] = useState(null);
  const [desiredSize, setDesiredSize] = useState(() => normalizeSize(30));
  const [currentStep, setCurrentStep] = useState(0);
  const [frameProgress, setFrameProgress] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [speedMs, setSpeedMs] = useState(100);

  const activeFrame = useMemo(() => {
    if (history.length === 0) {
      return null;
    }
    return history[Math.min(currentStep, history.length - 1)];
  }, [history, currentStep]);

  const activeParticles = activeFrame?.particles ?? [];
  const globalBestPath = activeFrame?.global_best?.path ?? solution?.path ?? [];

  const drawMaze = () => {
    const canvas = canvasRef.current;
    if (!canvas || maze.length === 0) {
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
        ctx.fillStyle = cell === 1 ? '#1e293b' : '#f8fafc';
        ctx.fillRect(cIdx * CELL_SIZE, rIdx * CELL_SIZE, CELL_SIZE, CELL_SIZE);
      });
    });

    ctx.strokeStyle = '#334155';
    ctx.strokeRect(0, 0, canvas.width, canvas.height);
    const drawPath = (pathPoints, color, width, alpha = 1) => {
      if (!pathPoints || pathPoints.length === 0) return;
      const progress = isRunning ? frameProgress : 1;
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

    if (activeParticles.length > 0) {
      activeParticles.forEach((particle, index) => {
        const hue = Math.round((index / activeParticles.length) * 360);
        const color = `hsla(${hue}, 70%, 65%, 0.65)`;
        drawPath(particle.path, color, CELL_SIZE / 4, 0.5);
        const visibleCount = Math.max(1, Math.floor(particle.path.length * (isRunning ? frameProgress : 1)));
        const last = particle.path?.[Math.min(visibleCount - 1, particle.path.length - 1)];
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

    if (globalBestPath.length > 0) {
      drawPath(globalBestPath, '#ff0000ff', CELL_SIZE / 2.5, 1);
    }

    const start = solution?.start;
    const goal = solution?.goal;
    if (start) {
      ctx.fillStyle = '#10b981';
      ctx.fillRect(
        start[1] * CELL_SIZE,
        start[0] * CELL_SIZE,
        CELL_SIZE,
        CELL_SIZE,
      );
    }
    if (goal) {
      ctx.fillStyle = '#ef4444';
      ctx.fillRect(goal[1] * CELL_SIZE, goal[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    }
  };

  useEffect(() => {
    drawMaze();
  }, [maze, activeParticles, globalBestPath, solution, frameProgress, isRunning]);

  useEffect(() => {
    if (!isRunning || history.length === 0) {
      return undefined;
    }
    let frameId;
    let lastTime = performance.now();

    const stepDuration = Math.max(20, Math.min(500, speedMs));

    const tick = (time) => {
      const delta = time - lastTime;
      lastTime = time;
      setFrameProgress((prev) => {
        const next = prev + delta / stepDuration;
        if (next >= 1) {
          setCurrentStep((prevStep) => {
            if (prevStep >= history.length - 1) {
              setIsRunning(false);
              return prevStep;
            }
            return prevStep + 1;
          });
          return next - 1;
        }
        return next;
      });
      frameId = requestAnimationFrame(tick);
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [isRunning, history.length, speedMs]);

  const fetchMaze = async (sizeOverride = desiredSize) => {
    setLoading(true);
    setError('');
    try {
      const url = new URL(`${API_BASE}/visuals/maze`);
      url.searchParams.set('size', sizeOverride);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch maze data');
      }
      const data = await response.json();
      setMaze(data.grid ?? []);
      setMazeSeed(data.seed ?? null);
      setSolution(null);
      setMazeSize(data.size ?? sizeOverride);
      setHistory([]);
      setCurrentStep(0);
      setFrameProgress(0);
      setIsRunning(false);
      return data.seed ?? null;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchSolution = async (sizeOverride = desiredSize, seedOverride = mazeSeed) => {
    setLoading(true);
    setError('');
    try {
      const url = new URL(`${API_BASE}/visuals/pso`);
      url.searchParams.set('size', sizeOverride);
      if (seedOverride !== null && seedOverride !== undefined) {
        url.searchParams.set('maze_seed', seedOverride);
      }
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to run solver');
      }
      const data = await response.json();
      setMaze(data.maze ?? []);
      setSolution(data.solution ?? null);
      setMazeSize(data.size ?? sizeOverride);
      setMazeSeed(data.maze_seed ?? seedOverride);
      const historyData = data.solution?.history ?? [];
      setHistory(historyData);
      setCurrentStep(0);
      setFrameProgress(0);
      setIsRunning(historyData.length > 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    if (desiredSize < MIN_SIZE || desiredSize > MAX_SIZE || desiredSize % 5 !== 0) {
      setError(`Maze size must be a multiple of 5 between ${MIN_SIZE} and ${MAX_SIZE}.`);
      return;
    }
    let seed = mazeSeed;
    if (seed === null) {
      seed = await fetchMaze(desiredSize);
    }
    if (seed === null || seed === undefined) {
      return;
    }
    fetchSolution(desiredSize, seed);
  };

  const handleStop = () => {
    setIsRunning(false);
  };

  const handleReset = () => {
    setIsRunning(false);
    setMaze([]);
    setHistory([]);
    setSolution(null);
    setMazeSize(null);
    setCurrentStep(0);
    setFrameProgress(0);
    setError('');
  };

  const statusText = useMemo(() => {
    if (!solution) {
      return 'Ready to start visualizing the maze solver.';
    }
    if (solution.solved) {
      return `Solved in ${solution.path.length} steps.`;
    }
    return 'Solver is exploring...';
  }, [solution]);

  const adjustSize = (delta) => {
    setDesiredSize((prev) => normalizeSize(prev + delta));
  };

  const handleSizeInput = (value) => {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) {
      return;
    }
    setDesiredSize(normalizeSize(parsed));
  };

  useEffect(() => {
    setIsRunning(false);
    setCurrentStep(0);
    setFrameProgress(0);
    if (desiredSize >= MIN_SIZE && desiredSize <= MAX_SIZE && desiredSize % 5 === 0) {
      fetchMaze(desiredSize);
    }
  }, [desiredSize]);

  return (
    <div className="app">
      <header>
        <h1>Maze Solver Visualizer</h1>
      </header>

      <div className="controls">
        <div className="size-control">
          <div className="size-input-group">
            <button type="button" onClick={() => adjustSize(-5)}>-</button>
            <input
              type="number"
              min={MIN_SIZE}
              max={MAX_SIZE}
              step="5"
              value={desiredSize}
              onChange={(event) => handleSizeInput(event.target.value)}
            />
            <button type="button" onClick={() => adjustSize(5)}>+</button>
          </div>
        </div>
        <div className="speed-control">
          <span>Animation speed ({speedMs} ms)</span>
          <input
            type="range"
            min="20"
            max="500"
            step="10"
            value={speedMs}
            onChange={(event) => setSpeedMs(Number(event.target.value))}
          />
        </div>
        <button onClick={handleStart} disabled={loading || isRunning}>
          Start
        </button>
        <button
          onClick={() => fetchMaze(desiredSize)}
          disabled={loading}
        >
          Generate Maze
        </button>
        <button onClick={handleStop} disabled={!isRunning}>
          Stop
        </button>
        <button onClick={handleReset} disabled={loading}>
          Reset
        </button>
      </div>

      {error && <div className="status error">{error}</div>}
      <div className="status">{loading ? 'Loading data...' : statusText}</div>

      <section className="visuals">
        <canvas ref={canvasRef} />
        <div className="details">
          <h2>Playback Details</h2>
          <ul>
            <li>Maze size: {mazeSize ?? (maze.length ? `${maze.length} x ${maze[0].length}` : '-')}</li>
            <li>Particles tracked: {activeParticles.length || solution?.swarm_size || '-'}</li>
            <li>Iterations recorded: {history.length}</li>
            <li>Current frame: {history.length ? `${currentStep + 1}/${history.length}` : '-'}</li>
            <li>
              Global best fitness:{' '}
              {activeFrame?.global_best?.fitness?.toFixed(2) ?? solution?.best_fitness ?? '-'}
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}

export default App;
