import { useRef, useEffect, useState } from 'react';
import './App.css';
import AntColonyControls from './algorithms/AntColonyControls';
import FireflyControls from './algorithms/FireflyControls';
import GeneticControls from './algorithms/GeneticControls';
import PsoControls from './algorithms/PsoControls';
import { drawMaze as drawMazeOnCanvas } from './mazeRenderer';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const MIN_SIZE = 15;
const MAX_SIZE = 100;

const ALGORITHMS = [
  { id: 'pso', label: 'Particle Swarm', name: 'Particle Swarm Optimization' },
  { id: 'genetic', label: 'Genetic Algorithm', name: 'Genetic Algorithm' },
  { id: 'firefly', label: 'Firefly Algorithm', name: 'Firefly Algorithm' },
  { id: 'ant', label: 'Ant Colony', name: 'Ant Colony Optimization' },
];

const EXPLANATIONS = {
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

const clamp = (val) => Math.max(MIN_SIZE, Math.min(MAX_SIZE, Math.round(val / 5) * 5));

const fetchApi = async (path, params) => {
  const url = new URL(`${API_BASE}/visuals/${path}`);
  Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v));
  const res = await fetch(url);
  if (!res.ok) throw new Error('API request failed');
  return res.json();
};

function App() {
  const canvasRef = useRef(null);
  
  const [state, setState] = useState({
    maze: [],
    history: [],
    solution: null,
    algorithm: 'pso',
    mazeSize: null,
    mazeSeed: null,
    desiredSize: 15,
    currentStep: 0,
    frameProgress: 0,
    isRunning: false,
    loading: false,
    error: '',
    speedMs: 100,
    runFailed: false,
    iterations: 240,
    swarmSize: 70,
    gaPopulation: 80,
    gaGenerations: 120,
    gaMutationRate: 0.05,
  });

  const update = (changes) => setState(s => ({ ...s, ...changes }));

  const resetPlayback = () => update({
    isRunning: false,
    history: [],
    currentStep: 0,
    frameProgress: 0,
  });

  const fetchMaze = async (size = state.desiredSize) => {
    update({ loading: true, error: '', runFailed: false });
    try {
      const data = await fetchApi('maze', { size });
      update({
        maze: data.grid ?? [],
        mazeSeed: data.seed ?? null,
        solution: null,
        mazeSize: data.size ?? size,
      });
      resetPlayback();
      return data.seed ?? null;
    } catch (err) {
      update({ error: err.message });
    } finally {
      update({ loading: false });
    }
    return null;
  };

  const runSolver = async () => {
    const { desiredSize, mazeSeed, algorithm } = state;
    
    if (desiredSize < MIN_SIZE || desiredSize > MAX_SIZE || desiredSize % 5 !== 0) {
      update({ error: `Size must be 5-step multiple between ${MIN_SIZE}-${MAX_SIZE}` });
      return;
    }

    const params = { size: desiredSize, maze_seed: mazeSeed };
    
    if (algorithm === 'pso') {
      if (state.iterations <= 0 || state.swarmSize <= 0) {
        update({ error: 'Iterations and swarm size must be positive' });
        return;
      }
      params.iterations = state.iterations;
      params.swarm_size = state.swarmSize;
    } else if (algorithm === 'genetic') {
      if (state.gaPopulation <= 0 || state.gaGenerations <= 0) {
        update({ error: 'Population and generations must be positive' });
        return;
      }
      if (state.gaMutationRate <= 0 || state.gaMutationRate > 1) {
        update({ error: 'Mutation rate must be between 0 and 1' });
        return;
      }
      params.population_size = state.gaPopulation;
      params.generations = state.gaGenerations;
      params.mutation_rate = state.gaMutationRate;
    } else {
      const algo = ALGORITHMS.find(a => a.id === algorithm);
      update({ error: `${algo?.name} visualisation coming soon` });
      return;
    }

    update({ error: '' });
    let seed = params.maze_seed;
    if (!seed) {
      seed = await fetchMaze(desiredSize);
      if (!seed) return;
      params.maze_seed = seed;
    }

    update({ loading: true, error: '', runFailed: false });
    try {
      const data = await fetchApi(algorithm, params);
      const hist = data.solution?.history ?? [];
      const solved = Boolean(data.solution?.solved);
      
      update({
        maze: data.maze ?? [],
        solution: data.solution ?? null,
        mazeSize: data.size ?? desiredSize,
        mazeSeed: data.maze_seed ?? seed,
        history: hist,
        runFailed: !solved,
        currentStep: !solved && hist.length > 0 ? hist.length - 1 : 0,
        frameProgress: !solved && hist.length > 0 ? 1 : 0,
        isRunning: solved && hist.length > 0,
      });
    } catch (err) {
      update({ error: err.message, runFailed: true });
    } finally {
      update({ loading: false });
    }
  };

  const handleReset = () => {
    resetPlayback();
    update({
      maze: [],
      solution: null,
      mazeSize: null,
      mazeSeed: null,
      error: '',
      runFailed: false,
    });
  };

  // Playback animation loop
  useEffect(() => {
    if (!state.isRunning || !state.history.length) return;
    
    let frameId;
    let lastTime = performance.now();
    const stepDur = Math.max(20, Math.min(1000, state.speedMs));

    const tick = (time) => {
      const delta = time - lastTime;
      lastTime = time;
      
      setState(s => {
        const nextProgress = s.frameProgress + delta / stepDur;
        if (nextProgress >= 1) {
          const nextStep = s.currentStep + 1;
          if (nextStep >= s.history.length) {
            return { ...s, isRunning: false };
          }
          return { ...s, currentStep: nextStep, frameProgress: nextProgress - 1 };
        }
        return { ...s, frameProgress: nextProgress };
      });
      
      frameId = requestAnimationFrame(tick);
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [state.isRunning, state.history.length, state.speedMs]);

  // Auto-fetch maze on size change
  useEffect(() => {
    resetPlayback();
    const { desiredSize } = state;
    if (desiredSize >= MIN_SIZE && desiredSize <= MAX_SIZE && desiredSize % 5 === 0) {
      fetchMaze(desiredSize);
    }
  }, [state.desiredSize]);

  // Clear solution on algorithm change
  useEffect(() => {
    resetPlayback();
    update({ solution: null, error: '', runFailed: false });
  }, [state.algorithm]);

  // Canvas rendering
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const frame = state.history[Math.min(state.currentStep, state.history.length - 1)];
    const fallbackCandidates = state.solution?.final_candidates ?? [];
    const explorers = frame?.candidates ?? fallbackCandidates;
    const frameBest = frame?.best ?? state.solution?.best_candidate ?? null;
    const bestPath = frameBest?.path ?? state.solution?.path ?? [];

    drawMazeOnCanvas({
      canvas: canvasRef.current,
      maze: state.maze,
      explorers,
      bestPath,
      solution: state.solution,
      frameProgress: state.frameProgress,
      isRunning: state.isRunning,
    });
  }, [canvasRef, state.maze, state.history, state.currentStep, state.solution, 
      state.frameProgress, state.isRunning]);

  // Computed values
  const algo = ALGORITHMS.find(a => a.id === state.algorithm);
  const isGenetic = state.algorithm === 'genetic';
  
  const sizeLabel = state.mazeSize ?? (state.maze.length ? 
    `${state.maze.length} x ${state.maze[0].length}` : '-');
  
  const frame = state.history[state.currentStep];
  const explorers = frame?.candidates ?? state.solution?.final_candidates ?? [];
  const trackedCount = explorers.length || 
    (isGenetic ? state.solution?.population_size : state.solution?.swarm_size) || '-';

  const currentFrameLabel = state.history.length ?
    `${isGenetic ? 'Generation' : 'Iteration'} ${Math.min(state.currentStep + 1, state.history.length)}/${state.history.length}` : '-';

  const frameBest = frame?.best ?? state.solution?.best_candidate ?? null;
  const fitness = frameBest?.fitness ?? state.solution?.best_fitness ?? null;
  const bestFitness = typeof fitness === 'number' ? fitness.toFixed(2) : '-';

  const statusText = state.runFailed ? 'Search failed.' :
    !state.solution ? 'Ready to start visualising the maze solver.' :
    state.solution.solved ? `Solved in ${state.solution.path.length} steps.` :
    'Solver is exploring...';

  const algorithmControls = (() => {
    switch (state.algorithm) {
      case 'pso':
        return <PsoControls
          iterations={state.iterations}
          swarmSize={state.swarmSize}
          iterationsPlaceholder={240}
          swarmPlaceholder={70}
          onIterationsChange={v => update({ iterations: v })}
          onSwarmSizeChange={v => update({ swarmSize: v })}
        />;
      case 'genetic':
        return <GeneticControls
          populationSize={state.gaPopulation}
          generations={state.gaGenerations}
          mutationRate={state.gaMutationRate}
          onPopulationChange={v => update({ gaPopulation: v })}
          onGenerationsChange={v => update({ gaGenerations: v })}
          onMutationRateChange={v => update({ gaMutationRate: v })}
        />;
      case 'firefly':
        return <FireflyControls />;
      default:
        return <AntColonyControls />;
    }
  })();

  return (
    <div className="app">
      <header>
        <h1>Maze Solver Visualiser</h1>
      </header>

      <div className="algorithm-selector">
        {ALGORITHMS.map(a => (
          <button
            key={a.id}
            type="button"
            className={a.id === state.algorithm ? 'active' : ''}
            onClick={() => update({ algorithm: a.id })}
          >
            {a.label}
          </button>
        ))}
      </div>

      <div className="controls">
        <div className="size-control">
          <div className="size-input-group">
            <button type="button" onClick={() => update({ desiredSize: clamp(state.desiredSize - 5) })}>-</button>
            <input
              type="number"
              min={MIN_SIZE}
              max={MAX_SIZE}
              step="5"
              value={state.desiredSize}
              onChange={e => update({ desiredSize: clamp(Number(e.target.value)) })}
            />
            <button type="button" onClick={() => update({ desiredSize: clamp(state.desiredSize + 5) })}>+</button>
          </div>
        </div>
        <div className="speed-control">
          <span>Animation speed ({state.speedMs} ms)</span>
          <input
            type="range"
            min="20"
            max="1000"
            step="10"
            value={state.speedMs}
            onChange={e => update({ speedMs: Number(e.target.value) })}
          />
        </div>
        <button onClick={runSolver} disabled={state.loading || state.isRunning}>Start</button>
        <button onClick={() => fetchMaze()} disabled={state.loading}>Generate Maze</button>
        <button onClick={() => update({ isRunning: false })} disabled={!state.isRunning}>Stop</button>
        <button onClick={handleReset} disabled={state.loading}>Reset</button>
      </div>

      {state.error && <div className="status error">{state.error}</div>}
      <div className="status">{state.loading ? 'Loading data...' : statusText}</div>

      <section className="visuals">
        <canvas ref={canvasRef} />
        <div className="details">
          <h2>Playback Details</h2>
          <ul>
            <li>Algorithm: {algo?.name}</li>
            <li>Maze size: {sizeLabel}</li>
            <li>{isGenetic ? 'Population' : 'Particles'} tracked: {trackedCount}</li>
            <li>{isGenetic ? 'Generations' : 'Iterations'} recorded: {state.history.length}</li>
            <li>Current frame: {currentFrameLabel}</li>
            <li>Best fitness: {bestFitness}</li>
          </ul>
          {algorithmControls}
          {EXPLANATIONS[state.algorithm] && (
            <div className="explanation">
              <h3>How this method solves the maze</h3>
              <ul>
                {EXPLANATIONS[state.algorithm].map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default App;