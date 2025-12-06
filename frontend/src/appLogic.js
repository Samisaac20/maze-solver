import { useEffect, useMemo, useState } from 'react';
import { drawMaze as drawMazeOnCanvas } from './mazeRenderer';

export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

export const ALGORITHMS = [
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

const ALGORITHM_EXPLANATIONS = {
  pso: [
    'Launch a swarm of explorers from the maze entrance.',
    'Each explorer remembers its best position while the swarm tracks the global best route.',
    'They drift toward both memories with a nudge of randomness to stay curious.',
    'The best path emerges where most explorers consistently converge.',
  ],
  genetic: [
    'Generate a population of complete maze routes, even if many are rough.',
    'Score every route by distance, coverage, and efficiency.',
    'Keep the fittest, mix them, and mutate small sections to produce new paths.',
    'Repeat until one offspring reaches the exit.',
  ],
  firefly: [
    'Treat each candidate route as a glowing firefly.',
    'Brighter routes pull nearby ones toward the same corridor.',
    'Random steps keep the swarm from clumping too early.',
    'Brightness grows until a path reaches the exit.',
  ],
  ant: [
    'Send simulated ants through the maze while they drop pheromones on good tiles.',
    'Shorter or more promising paths collect stronger pheromone trails.',
    'Bolder trails attract later ants, reinforcing useful passages.',
    'Eventually the pheromone map reveals a continuous route to the exit.',
  ],
};

export const MIN_SIZE = 15;
export const MAX_SIZE = 100;
const SIZE_STEP = 5;
const DEFAULT_SIZE = 15;

const BASE_PSO_ITERATIONS = 240;
const BASE_PSO_SWARM = 70;

const getDefaultPsoParams = () => ({
  iterations: BASE_PSO_ITERATIONS,
  swarmSize: BASE_PSO_SWARM,
});

const clampSize = (value) => {
  if (!Number.isFinite(value)) {
    return DEFAULT_SIZE;
  }
  const rounded = Math.round(value / SIZE_STEP) * SIZE_STEP;
  return Math.max(MIN_SIZE, Math.min(MAX_SIZE, rounded));
};

const buildUrl = (path, params = {}) => {
  const url = new URL(`${API_BASE}/visuals/${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      url.searchParams.set(key, value);
    }
  });
  return url;
};

const toErrorMessage = (error) => (error instanceof Error ? error.message : 'Unknown error');

export const useMazeSolver = (canvasRef) => {
  const defaultPso = useMemo(getDefaultPsoParams, []);

  const [maze, setMaze] = useState([]);
  const [history, setHistory] = useState([]);
  const [solution, setSolution] = useState(null);
  const [activeAlgorithm, setActiveAlgorithm] = useState('pso');
  const [mazeSize, setMazeSize] = useState(null);
  const [mazeSeed, setMazeSeed] = useState(null);
  const [desiredSize, setDesiredSize] = useState(clampSize(DEFAULT_SIZE));
  const [iterations, setIterations] = useState(defaultPso.iterations);
  const [swarmSize, setSwarmSize] = useState(defaultPso.swarmSize);
  const [gaPopulation, setGaPopulation] = useState(80);
  const [gaGenerations, setGaGenerations] = useState(120);
  const [gaMutationRate, setGaMutationRate] = useState(0.05);
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

  const psoSuggestions = defaultPso;

  const explanationPoints = useMemo(
    () => ALGORITHM_EXPLANATIONS[activeAlgorithm] ?? [],
    [activeAlgorithm],
  );

  const resetPlayback = () => {
    setIsRunning(false);
    setHistory([]);
    setCurrentStep(0);
    setFrameProgress(0);
  };

  const updateSolverState = (data, fallbackSize, fallbackSeed) => {
    setMaze(data.maze ?? []);
    setSolution(data.solution ?? null);
    setMazeSize(data.size ?? fallbackSize);
    setMazeSeed(data.maze_seed ?? fallbackSeed);

    const historyData = data.solution?.history ?? [];
    setHistory(historyData);

    const solved = Boolean(data.solution?.solved);
    setRunFailed(!solved);

    if (!solved && historyData.length > 0) {
      setCurrentStep(historyData.length - 1);
      setFrameProgress(1);
      setIsRunning(false);
      return;
    }

    setCurrentStep(0);
    setFrameProgress(0);
    setIsRunning(historyData.length > 0);
  };

  const fetchMaze = async (sizeOverride = desiredSize) => {
    setLoading(true);
    setError('');
    setRunFailed(false);
    try {
      const response = await fetch(buildUrl('maze', { size: sizeOverride }));
      if (!response.ok) {
        throw new Error('Failed to fetch maze data');
      }
      const data = await response.json();
      setMaze(data.grid ?? []);
      setMazeSeed(data.seed ?? null);
      setSolution(null);
      setMazeSize(data.size ?? sizeOverride);
      resetPlayback();
      return data.seed ?? null;
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setLoading(false);
    }
    return null;
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
      const response = await fetch(buildUrl('pso', {
        size: sizeOverride,
        maze_seed: seedOverride,
        iterations: iterationsOverride,
        swarm_size: swarmOverride,
      }));
      if (!response.ok) {
        throw new Error('Failed to run solver');
      }
      const data = await response.json();
      updateSolverState(data, sizeOverride, seedOverride);
    } catch (err) {
      setError(toErrorMessage(err));
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
      const response = await fetch(buildUrl('genetic', {
        size: sizeOverride,
        maze_seed: seedOverride,
        population_size: populationOverride,
        generations: generationOverride,
        mutation_rate: mutationOverride,
      }));
      if (!response.ok) {
        throw new Error('Failed to run solver');
      }
      const data = await response.json();
      updateSolverState(data, sizeOverride, seedOverride);
    } catch (err) {
      setError(toErrorMessage(err));
      setRunFailed(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isRunning || history.length === 0) {
      return undefined;
    }
    let frameId;
    let lastTime = performance.now();
    const stepDuration = Math.max(20, Math.min(1000, speedMs));

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

  useEffect(() => {
    resetPlayback();
    if (desiredSize >= MIN_SIZE && desiredSize <= MAX_SIZE && desiredSize % SIZE_STEP === 0) {
      fetchMaze(desiredSize);
    }
  }, [desiredSize]);

  useEffect(() => {
    resetPlayback();
    setSolution(null);
    setError('');
    setRunFailed(false);
  }, [activeAlgorithm]);

  const handleStart = async () => {
    if (desiredSize < MIN_SIZE || desiredSize > MAX_SIZE || desiredSize % SIZE_STEP !== 0) {
      setError(`Maze size must be a multiple of ${SIZE_STEP} between ${MIN_SIZE} and ${MAX_SIZE}.`);
      return;
    }

    if (isPsoActive) {
      if ((iterations ?? 0) <= 0 || (swarmSize ?? 0) <= 0) {
        setError('Iterations and swarm size must be positive.');
        return;
      }
    }

    if (isGeneticActive) {
      if (gaPopulation <= 0 || gaGenerations <= 0) {
        setError('Population size and generations must be positive.');
        return;
      }
      if (Number.isNaN(gaMutationRate) || gaMutationRate <= 0 || gaMutationRate > 1) {
        setError('Mutation rate must be between 0 and 1.');
        return;
      }
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
      fetchPsoSolution(desiredSize, seed, iterations ?? psoSuggestions.iterations, swarmSize ?? psoSuggestions.swarmSize);
    } else if (isGeneticActive) {
      fetchGeneticSolution(desiredSize, seed, gaPopulation, gaGenerations, gaMutationRate);
    } else {
      setError(`${algorithmDisplay} visualisation is coming soon.`);
    }
  };

  const handleStop = () => setIsRunning(false);

  const handleReset = () => {
    resetPlayback();
    setMaze([]);
    setSolution(null);
    setMazeSize(null);
    setMazeSeed(null);
    setError('');
    setRunFailed(false);
  };

  const adjustSize = (delta) => {
    setDesiredSize((prev) => clampSize(prev + delta));
  };

  const handleSizeInput = (value) => {
    const parsed = Number(value);
    if (Number.isNaN(parsed)) {
      return;
    }
    setDesiredSize(clampSize(parsed));
  };

  const activeFrame = useMemo(() => {
    if (history.length === 0) {
      return null;
    }
    return history[Math.min(currentStep, history.length - 1)];
  }, [history, currentStep]);

  const fallbackCandidates = useMemo(() => solution?.final_candidates ?? [], [solution]);

  const activeExplorers = useMemo(() => {
    if (activeFrame) {
      return activeFrame.candidates ?? fallbackCandidates;
    }
    return fallbackCandidates;
  }, [activeFrame, fallbackCandidates]);

  const frameBest = activeFrame?.best ?? solution?.best_candidate ?? null;
  const bestPath = frameBest?.path ?? solution?.path ?? [];
  const bestFitness = frameBest?.fitness ?? solution?.best_fitness ?? null;

  useEffect(() => {
    if (!canvasRef.current) {
      return;
    }
    drawMazeOnCanvas({
      canvas: canvasRef.current,
      maze,
      explorers: activeExplorers,
      bestPath,
      solution,
      frameProgress,
      isRunning,
    });
  }, [canvasRef, maze, activeExplorers, bestPath, solution, frameProgress, isRunning]);

  const trackedLabel = isGeneticActive ? 'Population tracked' : 'Particles tracked';
  const recordedLabel = isGeneticActive ? 'Generations recorded' : 'Iterations recorded';
  const playbackLabel = isGeneticActive ? 'Generation' : 'Iteration';

  const trackedCount =
    activeExplorers.length
    || solution?.final_candidates?.length
    || (isGeneticActive ? solution?.population_size : solution?.swarm_size)
    || '-';

  const currentFrameLabel = history.length
    ? `${playbackLabel} ${Math.min(currentStep + 1, history.length)}/${history.length}`
    : '-';

  const bestFitnessDisplay = typeof bestFitness === 'number' ? bestFitness.toFixed(2) : '-';

  const statusText = useMemo(() => {
    if (runFailed) {
      return 'Search failed.';
    }
    if (!solution) {
      return 'Ready to start visualising the maze solver.';
    }
    if (solution.solved) {
      return `Solved in ${solution.path.length} steps.`;
    }
    return 'Solver is exploring...';
  }, [solution, runFailed]);

  return {
    maze,
    activeAlgorithm,
    setActiveAlgorithm,
    desiredSize,
    adjustSize,
    handleSizeInput,
    iterations,
    setIterations,
    swarmSize,
    setSwarmSize,
    gaPopulation,
    setGaPopulation,
    gaGenerations,
    setGaGenerations,
    gaMutationRate,
    setGaMutationRate,
    setSpeedMs,
    speedMs,
    handleStart,
    fetchMaze,
    handleStop,
    handleReset,
    loading,
    isRunning,
    error,
    statusText,
    algorithmDisplay,
    mazeSize,
    trackedLabel,
    trackedCount,
    recordedLabel,
    historyLength: history.length,
    currentFrameLabel,
    bestFitnessDisplay,
    explanationPoints,
    psoSuggestions,
  };
};
