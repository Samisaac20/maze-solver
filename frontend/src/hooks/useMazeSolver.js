import { useState, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const MIN_SIZE = 15;
const MAX_SIZE = 100;

const clamp = (val) => Math.max(MIN_SIZE, Math.min(MAX_SIZE, Math.round(val / 5) * 5));

const fetchApi = async (path, params) => {
  const url = new URL(`${API_BASE}/visuals/${path}`);
  Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v));
  const res = await fetch(url);
  if (!res.ok) throw new Error('API request failed');
  return res.json();
};

export const useMazeSolver = () => {
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
    fireflyCount: 60,
    fireflyAbsorption: 1.0,
    fireflyIterations: 200,
    fireflyRandomness: 0.2,
    antCount: 60,
    antIterations: 150,
    antEvaporationRate: 0.5,
    antAlpha: 1.0,
    antBeta: 2.0,
    showVelocities: true,
    showHeatmap: true,
    showTopPerformers: true,
    showMetrics: true,
    showPheromones: true,
    selectedPreset: 'medium',
    mazeAnalysis: null,
  });

  const update = useCallback((changes) => {
    setState(s => ({ ...s, ...changes }));
  }, []);

  const resetPlayback = useCallback(() => {
    update({
      isRunning: false,
      history: [],
      currentStep: 0,
      frameProgress: 0,
    });
  }, [update]);

  const getComplexityParams = useCallback(() => {
    return { preset: state.selectedPreset };
  }, [state.selectedPreset]);

  const fetchMaze = useCallback(async (size = state.desiredSize) => {
    update({ loading: true, error: '', runFailed: false });
    try {
      const params = { size, ...getComplexityParams() };
      const data = await fetchApi('maze', params);
      update({
        maze: data.grid ?? [],
        mazeSeed: data.seed ?? null,
        solution: null,
        mazeSize: data.size ?? size,
        mazeAnalysis: data.analysis ?? null,
      });
      resetPlayback();
      return data.seed ?? null;
    } catch (err) {
      update({ error: err.message });
    } finally {
      update({ loading: false });
    }
    return null;
  }, [state.desiredSize, update, getComplexityParams, resetPlayback]);

  const runSolver = useCallback(async () => {
    const { desiredSize, mazeSeed, algorithm } = state;

    if (desiredSize < MIN_SIZE || desiredSize > MAX_SIZE || desiredSize % 5 !== 0) {
      update({ error: `Size must be 5-step multiple between ${MIN_SIZE}-${MAX_SIZE}` });
      return;
    }

    const params = {
      size: desiredSize,
      maze_seed: mazeSeed,
      ...getComplexityParams()
    };

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
    } else if (algorithm === 'firefly') {
      if (state.fireflyCount <= 0 || state.fireflyIterations <= 0) {
        update({ error: 'Fireflies and iterations must be positive' });
        return;
      }
      if (state.fireflyAbsorption < 0.1 || state.fireflyAbsorption > 5.0) {
        update({ error: 'Absorption must be between 0.1 and 5.0' });
        return;
      }
      params.fireflies = state.fireflyCount;
      params.absorption = state.fireflyAbsorption;
      params.iterations = state.fireflyIterations;
      params.randomness = state.fireflyRandomness;
    } else if (algorithm === 'ant') {
      if (state.antCount <= 0 || state.antIterations <= 0) {
        update({ error: 'Ants and iterations must be positive' });
        return;
      }
      if (state.antEvaporationRate < 0.1 || state.antEvaporationRate > 0.9) {
        update({ error: 'Evaporation rate must be between 0.1 and 0.9' });
        return;
      }
      params.ants = state.antCount;
      params.iterations = state.antIterations;
      params.evaporation_rate = state.antEvaporationRate;
      params.alpha = state.antAlpha;
      params.beta = state.antBeta;
    }

    update({ error: '' });
    let seed = params.maze_seed;
    if (!seed) {
      seed = await fetchMaze(desiredSize);
      if (!seed) return;
      params.maze_seed = seed;
      Object.assign(params, getComplexityParams());
    }

    update({ loading: true, error: '', runFailed: false });
    try {
      const apiAlgorithm = algorithm === 'ant' ? 'ant-colony' : algorithm;
      const data = await fetchApi(apiAlgorithm, params);
      const hist = data.solution?.history ?? [];
      const solved = Boolean(data.solution?.solved);

      update({
        maze: data.maze ?? [],
        solution: data.solution ?? null,
        mazeSize: data.size ?? desiredSize,
        mazeSeed: data.maze_seed ?? seed,
        mazeAnalysis: data.maze_analysis ?? null,
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
  }, [state, update, fetchMaze, getComplexityParams]);

  const handleReset = useCallback(() => {
    resetPlayback();
    update({
      maze: [],
      solution: null,
      mazeSize: null,
      mazeSeed: null,
      mazeAnalysis: null,
      error: '',
      runFailed: false,
    });
  }, [resetPlayback, update]);

  return {
    state,
    update,
    resetPlayback,
    fetchMaze,
    runSolver,
    handleReset,
  };
};

export const clampSize = clamp;
export { MIN_SIZE, MAX_SIZE };
