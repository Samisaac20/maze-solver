import { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';
import AntColonyControls from './algorithms/AntColonyControls';
import FireflyControls from './algorithms/FireflyControls';
import GeneticControls from './algorithms/GeneticControls';
import PsoControls from './algorithms/PsoControls';
import { drawMaze as drawMazeOnCanvas } from './mazeRenderer';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const ALGORITHMS = [
  { id: 'pso', label: 'Particle Swarm' },
  { id: 'genetic', label: 'Genetic Algorithm' },
  { id: 'firefly', label: 'Firefly Algorithm' },
  { id: 'ant', label: 'Ant Colony' },
];
const ALGORITHM_LABELS = {
  pso: 'Particle Swarm Optimization',
  genetic: 'Genetic Algorithm',
  firefly: 'Firefly Algorithm',
  ant: 'Ant Colony Optimization',
};

function App() {
  const canvasRef = useRef(null);
  const [maze, setMaze] = useState([]);
  const [history, setHistory] = useState([]);
  const [solution, setSolution] = useState(null);
  const [activeAlgorithm, setActiveAlgorithm] = useState('pso');
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
  const [iterations, setIterations] = useState(80);
  const [swarmSize, setSwarmSize] = useState(30);
  const [gaPopulation, setGaPopulation] = useState(80);
  const [gaGenerations, setGaGenerations] = useState(120);
  const [gaMutationRate, setGaMutationRate] = useState(0.08);
  const [currentStep, setCurrentStep] = useState(0);
  const [frameProgress, setFrameProgress] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [speedMs, setSpeedMs] = useState(100);
  const [runFailed, setRunFailed] = useState(false);
  const algorithmDisplay = ALGORITHM_LABELS[activeAlgorithm];
  const isPsoActive = activeAlgorithm === 'pso';
  const isGeneticActive = activeAlgorithm === 'genetic';

  const renderAlgorithmControls = () => {
    if (activeAlgorithm === 'pso') {
      return (
        <PsoControls
          iterations={iterations}
          swarmSize={swarmSize}
          onIterationsChange={setIterations}
          onSwarmSizeChange={setSwarmSize}
        />
      );
    }
    if (activeAlgorithm === 'genetic') {
      return (
        <GeneticControls
          populationSize={gaPopulation}
          generations={gaGenerations}
          mutationRate={gaMutationRate}
          onPopulationChange={setGaPopulation}
          onGenerationsChange={setGaGenerations}
          onMutationRateChange={setGaMutationRate}
        />
      );
    }
    if (activeAlgorithm === 'firefly') {
      return <FireflyControls />;
    }
    return <AntColonyControls />;
  };

  const activeFrame = useMemo(() => {
    if (history.length === 0) {
      return null;
    }
    return history[Math.min(currentStep, history.length - 1)];
  }, [history, currentStep]);

  const activeExplorers = useMemo(() => {
    if (!activeFrame) {
      return [];
    }
    if (isGeneticActive) {
      return activeFrame.population ?? [];
    }
    return activeFrame.particles ?? [];
  }, [activeFrame, isGeneticActive]);

  const frameBest = useMemo(() => {
    if (!activeFrame) {
      return null;
    }
    if (isGeneticActive) {
      return activeFrame.best ?? null;
    }
    return activeFrame.global_best ?? null;
  }, [activeFrame, isGeneticActive]);

  const bestPath = frameBest?.path ?? solution?.path ?? [];
  const bestFitness = frameBest?.fitness ?? solution?.best_fitness ?? null;

  const renderMaze = () => {
    drawMazeOnCanvas({
      canvas: canvasRef.current,
      maze,
      explorers: activeExplorers,
      bestPath,
      solution,
      frameProgress,
      isRunning,
    });
  };

  useEffect(() => {
    renderMaze();
  }, [maze, activeExplorers, bestPath, solution, frameProgress, isRunning]);

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
    setRunFailed(false);
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

  const fetchPsoSolution = async (
    sizeOverride = desiredSize,
    seedOverride = mazeSeed,
    iterationsOverride = iterations,
    swarmOverride = swarmSize,
  ) => {
    setLoading(true);
    setError('');
    setRunFailed(false);
    try {
      const url = new URL(`${API_BASE}/visuals/pso`);
      url.searchParams.set('size', sizeOverride);
      if (seedOverride !== null && seedOverride !== undefined) {
        url.searchParams.set('maze_seed', seedOverride);
      }
      url.searchParams.set('iterations', iterationsOverride);
      url.searchParams.set('swarm_size', swarmOverride);
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
      const solved = Boolean(data.solution?.solved);
      setRunFailed(!solved);
      if (!solved && historyData.length > 0) {
        setCurrentStep(historyData.length - 1);
        setFrameProgress(1);
        setIsRunning(false);
      } else {
        setCurrentStep(0);
        setFrameProgress(0);
        setIsRunning(historyData.length > 0);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setRunFailed(true);
    } finally {
      setLoading(false);
    }
  };

  const fetchGeneticSolution = async (
    sizeOverride = desiredSize,
    seedOverride = mazeSeed,
    populationOverride = gaPopulation,
    generationOverride = gaGenerations,
    mutationOverride = gaMutationRate,
  ) => {
    setLoading(true);
    setError('');
    setRunFailed(false);
    try {
      const url = new URL(`${API_BASE}/visuals/genetic`);
      url.searchParams.set('size', sizeOverride);
      if (seedOverride !== null && seedOverride !== undefined) {
        url.searchParams.set('maze_seed', seedOverride);
      }
      url.searchParams.set('population_size', populationOverride);
      url.searchParams.set('generations', generationOverride);
      url.searchParams.set('mutation_rate', mutationOverride);
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
      const solved = Boolean(data.solution?.solved);
      setRunFailed(!solved);
      if (!solved && historyData.length > 0) {
        setCurrentStep(historyData.length - 1);
        setFrameProgress(1);
        setIsRunning(false);
      } else {
        setCurrentStep(0);
        setFrameProgress(0);
        setIsRunning(historyData.length > 0);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setRunFailed(true);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    if (desiredSize < MIN_SIZE || desiredSize > MAX_SIZE || desiredSize % 5 !== 0) {
      setError(`Maze size must be a multiple of 5 between ${MIN_SIZE} and ${MAX_SIZE}.`);
      return;
    }
    if (isPsoActive) {
      if (iterations <= 0 || swarmSize <= 0) {
        setError('Iterations and swarm size must be positive integers.');
        return;
      }
    } else if (isGeneticActive) {
      if (gaPopulation <= 0 || gaGenerations <= 0) {
        setError('Population size and generations must be positive.');
        return;
      }
      if (Number.isNaN(gaMutationRate) || gaMutationRate <= 0 || gaMutationRate > 1) {
        setError('Mutation rate must be between 0 and 1.');
        return;
      }
    } else {
      setError(`${algorithmDisplay} visualisation is coming soon.`);
      return;
    }
    setError('');
    let seed = mazeSeed;
    if (seed === null) {
      seed = await fetchMaze(desiredSize);
    }
    if (seed === null || seed === undefined) {
      return;
    }
    if (isPsoActive) {
      fetchPsoSolution(desiredSize, seed, iterations, swarmSize);
    } else if (isGeneticActive) {
      fetchGeneticSolution(desiredSize, seed, gaPopulation, gaGenerations, gaMutationRate);
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
    setFrameProgress(0);
    setError('');
    setRunFailed(false);
  };

  const trackedLabel = isGeneticActive ? 'Population tracked' : 'Particles tracked';
  const recordedLabel = isGeneticActive ? 'Generations recorded' : 'Iterations recorded';
  const playbackLabel = isGeneticActive ? 'Generation' : 'Iteration';
  const trackedCount =
    activeExplorers.length
    || (isGeneticActive ? solution?.population_size : solution?.swarm_size)
    || '-';
  const currentFrameLabel = history.length
    ? `${playbackLabel} ${Math.min(currentStep + 1, history.length)}/${history.length}`
    : '-';
  const bestFitnessDisplay = typeof bestFitness === 'number' ? bestFitness.toFixed(2) : '-';

  const statusText = useMemo(() => {
    if (runFailed) {
      return 'search failed';
    }
    if (!solution) {
      return 'Ready to start visualizing the maze solver.';
    }
    if (solution.solved) {
      return `Solved in ${solution.path.length} steps.`;
    }
    return 'Solver is exploring...';
  }, [solution, runFailed]);

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

  useEffect(() => {
    setIsRunning(false);
    setHistory([]);
    setSolution(null);
    setCurrentStep(0);
    setFrameProgress(0);
    setError('');
    setRunFailed(false);
  }, [activeAlgorithm]);

  return (
    <div className="app">
      <header>
        <h1>Maze Solver Visualiser</h1>
      </header>

      <div className="algorithm-selector">
        {ALGORITHMS.map((algo) => (
          <button
            key={algo.id}
            type="button"
            className={algo.id === activeAlgorithm ? 'active' : ''}
            onClick={() => setActiveAlgorithm(algo.id)}
          >
            {algo.label}
          </button>
        ))}
      </div>

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
            <li>Algorithm: {algorithmDisplay}</li>
            <li>Maze size: {mazeSize ?? (maze.length ? `${maze.length} x ${maze[0].length}` : '-')}</li>
            <li>{trackedLabel}: {trackedCount}</li>
            <li>{recordedLabel}: {history.length}</li>
            <li>Current frame: {currentFrameLabel}</li>
            <li>Best fitness: {bestFitnessDisplay}</li>
          </ul>
          {renderAlgorithmControls()}
        </div>
      </section>
    </div>
  );
}

export default App;
