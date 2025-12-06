import { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const CELL_SIZE = 24;

function App() {
  const canvasRef = useRef(null);
  const [maze, setMaze] = useState([]);
  const [history, setHistory] = useState([]);
  const [solution, setSolution] = useState(null);
  const [mazeSize, setMazeSize] = useState(null);
  const [desiredSize, setDesiredSize] = useState(6);
  const [currentStep, setCurrentStep] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const activeFrame = useMemo(() => {
    if (history.length === 0) {
      return null;
    }
    return history[Math.min(currentStep, history.length - 1)];
  }, [history, currentStep]);

  const activePath = useMemo(() => {
    if (activeFrame?.path) {
      return activeFrame.path;
    }
    return solution?.path ?? [];
  }, [activeFrame, solution]);

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

    ctx.strokeStyle = '#cbd5f5';
    ctx.strokeRect(0, 0, canvas.width, canvas.height);

    if (activePath.length > 0) {
      ctx.strokeStyle = '#0ea5e9';
      ctx.lineWidth = CELL_SIZE / 3;
      ctx.lineCap = 'round';
      ctx.beginPath();
      activePath.forEach(([row, col], index) => {
        const x = col * CELL_SIZE + CELL_SIZE / 2;
        const y = row * CELL_SIZE + CELL_SIZE / 2;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();
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
  }, [maze, activePath, solution]);

  useEffect(() => {
    if (!isRunning || history.length === 0) {
      return () => {};
    }
    const intervalId = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= history.length - 1) {
          clearInterval(intervalId);
          setIsRunning(false);
          return prev;
        }
        return prev + 1;
      });
    }, 750);

    return () => clearInterval(intervalId);
  }, [isRunning, history]);

  const fetchVisualization = async (sizeOverride = desiredSize) => {
    setLoading(true);
    setError('');
    try {
      const url = new URL(`${API_BASE}/visuals/pso`);
      url.searchParams.set('size', sizeOverride);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch visualization data');
      }
      const data = await response.json();
      setMaze(data.maze ?? []);
      setSolution(data.solution ?? null);
      setMazeSize(data.size ?? sizeOverride);
      const historyData = data.solution?.history ?? [];
      setHistory(historyData);
      setCurrentStep(0);
      setIsRunning(historyData.length > 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleStart = () => {
    if (desiredSize < 2 || desiredSize % 2 !== 0) {
      setError('Maze size must be an even number equal to or greater than 2.');
      return;
    }
    if (maze.length === 0) {
      fetchVisualization(desiredSize);
    } else {
      setIsRunning(true);
    }
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

  return (
    <div className="app">
      <header>
        <div>
          <h1>Maze Solver Visualizer</h1>
          <p>Live playback of the FastAPI + PSO maze solving backend.</p>
        </div>
        <div className="controls">
          <label className="size-control">
            <span>Maze size (even)</span>
            <input
              type="number"
              min="2"
              step="2"
              value={desiredSize}
              onChange={(event) => setDesiredSize(Number(event.target.value))}
            />
          </label>
          <button onClick={handleStart} disabled={loading || isRunning}>
            {maze.length === 0 ? 'Start' : 'Resume'}
          </button>
          <button onClick={handleStop} disabled={!isRunning}>
            Stop
          </button>
          <button onClick={handleReset} disabled={loading}>
            Reset
          </button>
        </div>
      </header>

      {error && <div className="status error">{error}</div>}
      <div className="status">{loading ? 'Loading data...' : statusText}</div>

      <section className="visuals">
        <canvas ref={canvasRef} />
        <div className="details">
          <h2>Playback Details</h2>
          <ul>
            <li>Maze size: {mazeSize ?? (maze.length ? `${maze.length} x ${maze[0].length}` : '-')}</li>
            <li>Iterations recorded: {history.length}</li>
            <li>Current frame: {history.length ? `${currentStep + 1}/${history.length}` : '-'}</li>
            <li>Best fitness: {activeFrame?.best_fitness?.toFixed(2) ?? solution?.best_fitness ?? '-'}</li>
          </ul>
          <p>
            Use the buttons to start a new simulation, pause the animation, or reset the canvas.
            Update <code>VITE_API_BASE</code> in an env file if your backend runs elsewhere.
          </p>
        </div>
      </section>
    </div>
  );
}

export default App;
