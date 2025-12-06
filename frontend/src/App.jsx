import { useRef } from 'react';
import './App.css';
import AntColonyControls from './algorithms/AntColonyControls';
import FireflyControls from './algorithms/FireflyControls';
import GeneticControls from './algorithms/GeneticControls';
import PsoControls from './algorithms/PsoControls';
import { ALGORITHMS, MAX_SIZE, MIN_SIZE, useMazeSolver } from './appLogic';

function App() {
  const canvasRef = useRef(null);
  const {
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
    speedMs,
    setSpeedMs,
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
    historyLength,
    currentFrameLabel,
    bestFitnessDisplay,
    explanationPoints,
    psoSuggestions,
  } = useMazeSolver(canvasRef);

  const sizeLabel = mazeSize ?? (maze.length ? `${maze.length} x ${maze[0].length}` : '-');

  const algorithmControls = (() => {
    switch (activeAlgorithm) {
      case 'pso':
        return (
          <PsoControls
            iterations={iterations}
            swarmSize={swarmSize}
            iterationsPlaceholder={psoSuggestions.iterations}
            swarmPlaceholder={psoSuggestions.swarmSize}
            onIterationsChange={setIterations}
            onSwarmSizeChange={setSwarmSize}
          />
        );
      case 'genetic':
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
      case 'firefly':
        return <FireflyControls />;
      case 'ant':
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
            max="1000"
            step="10"
            value={speedMs}
            onChange={(event) => setSpeedMs(Number(event.target.value))}
          />
        </div>
        <button onClick={handleStart} disabled={loading || isRunning}>
          Start
        </button>
        <button
          onClick={() => fetchMaze()}
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
            <li>Maze size: {sizeLabel}</li>
            <li>{trackedLabel}: {trackedCount}</li>
            <li>{recordedLabel}: {historyLength}</li>
            <li>Current frame: {currentFrameLabel}</li>
            <li>Best fitness: {bestFitnessDisplay}</li>
          </ul>
          {algorithmControls}
          {explanationPoints.length > 0 && (
            <div className="explanation">
              <h3>How this method solves the maze</h3>
              <ul>
                {explanationPoints.map((point, index) => (
                  <li key={`${activeAlgorithm}-explain-${index}`}>{point}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default App;
