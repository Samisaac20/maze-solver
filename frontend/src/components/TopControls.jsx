import React from 'react';
import { clampSize } from '../hooks/useMazeSolver';

const ALGORITHMS = [
  { id: 'pso', label: 'Particle Swarm', name: 'Particle Swarm Optimization' },
  { id: 'genetic', label: 'Genetic Algorithm', name: 'Genetic Algorithm' },
  { id: 'firefly', label: 'Firefly Algorithm', name: 'Firefly Algorithm' },
  { id: 'ant', label: 'Ant Colony', name: 'Ant Colony Optimization' },
];

const COMPLEXITY_PRESETS = [
  { id: 'trivial', label: 'Trivial', description: 'Perfect maze, easiest' },
  { id: 'easy', label: 'Easy', description: 'Minimal complexity' },
  { id: 'medium', label: 'Medium', description: 'Balanced' },
  { id: 'hard', label: 'Hard', description: 'Challenging' },
  { id: 'extreme', label: 'Extreme', description: 'Maximum confusion' },
  { id: 'algorithm_test', label: 'Algorithm Test', description: 'XAI optimized' },
];

function TopControls({ state, update, runSolver, fetchMaze, handleReset }) {
  const { algorithm, loading, isRunning, error, selectedPreset, desiredSize, speedMs } = state;
  const isPso = algorithm === 'pso';
  const isGenetic = algorithm === 'genetic';
  const isAnt = algorithm === 'ant';
  const [xaiOpen, setXaiOpen] = React.useState(true);

  const statusText = state.runFailed ? 'Search failed.' :
    !state.solution ? 'Ready to start visualising the maze solver.' :
      state.solution.solved ? `Solved in ${state.solution.path.length} steps.` :
        'Solver is exploring...';

  return (
    <div className="top-controls">
      {/* LEFT COLUMN - Algorithm & Runner */}
      <div className="top-left">
        {/* Algorithm Selector */}
        <div className="control-section">
          <h3>Algorithm</h3>
          <div className="algorithm-selector">
            {ALGORITHMS.map(a => (
              <button
                key={a.id}
                type="button"
                className={a.id === algorithm ? 'active' : ''}
                onClick={() => update({ algorithm: a.id })}
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>

        {/* Runner Buttons */}
        <div className="control-section">
          <h3>Runner</h3>
          <div className="runner-buttons">
            <button onClick={runSolver} disabled={loading || isRunning}>
              Start Solver
            </button>
            <button onClick={() => fetchMaze()} disabled={loading}>
              New Maze
            </button>
            <button onClick={() => update({ isRunning: false })} disabled={!isRunning}>
              Stop
            </button>
            <button onClick={handleReset} disabled={loading}>
              Reset
            </button>
          </div>
        </div>

        {error && <div className="status error">{error}</div>}
        {!error && <div className="status">{loading ? 'Loading...' : statusText}</div>}
      </div>

      {/* RIGHT COLUMN - Settings & XAI */}
      <div className="top-right">
        {/* Complexity Slider */}
        <div className="control-section">
          <h3>Maze Complexity</h3>
          <div className="complexity-slider-main">
            <label>
              <span className="complexity-label">
                {COMPLEXITY_PRESETS.find(p => p.id === selectedPreset)?.label || 'Medium'}
                <span className="complexity-stars">
                  {COMPLEXITY_PRESETS.find(p => p.id === selectedPreset)?.stars}
                </span>
              </span>
              <input
                type="range"
                min="0"
                max="5"
                step="1"
                value={COMPLEXITY_PRESETS.findIndex(p => p.id === selectedPreset)}
                onChange={e => {
                  const preset = COMPLEXITY_PRESETS[Number(e.target.value)];
                  update({ selectedPreset: preset.id });
                }}
                className="complexity-range"
              />
              <div className="complexity-markers">
                {COMPLEXITY_PRESETS.map((preset, idx) => (
                  <span
                    key={preset.id}
                    className="complexity-marker"
                    style={{ left: `${(idx / (COMPLEXITY_PRESETS.length - 1)) * 100}%` }}
                  >
                    {preset.label}
                  </span>
                ))}
              </div>
            </label>
          </div>
        </div>

        {/* Size and Speed Controls */}
        <div className="control-section">
          <h3>Maze Settings</h3>
          <div className="maze-settings">
            <div className="size-control">
              <span>Size</span>
              <div className="size-input-group">
                <button type="button" onClick={() => update({ desiredSize: clampSize(desiredSize - 5) })}>-</button>
                <input
                  type="number"
                  min={15}
                  max={100}
                  step="5"
                  value={desiredSize}
                  onChange={e => update({ desiredSize: clampSize(Number(e.target.value)) })}
                />
                <button type="button" onClick={() => update({ desiredSize: clampSize(desiredSize + 5) })}>+</button>
              </div>
            </div>
            <div className="speed-control">
              <span>Animation Speed ({speedMs}ms)</span>
              <input
                type="range"
                min="20"
                max="1000"
                step="10"
                value={speedMs}
                onChange={e => update({ speedMs: Number(e.target.value) })}
              />
            </div>
          </div>
        </div>

        {/* XAI Toggles - Collapsible */}
        <div className="xai-section">
          <div className="xai-header" onClick={() => setXaiOpen(!xaiOpen)}>
            <h3>XAI Options</h3>
            <span className={`xai-arrow ${xaiOpen ? 'open' : ''}`}>▼</span>
          </div>
          <div className={`xai-toggles ${xaiOpen ? 'open' : ''}`}>
            {isPso && (
              <label className="xai-toggle">
                <input
                  type="checkbox"
                  checked={state.showVelocities}
                  onChange={e => update({ showVelocities: e.target.checked })}
                />
                <span>Velocity Vectors</span>
              </label>
            )}
            {isGenetic && (
              <label className="xai-toggle">
                <input
                  type="checkbox"
                  checked={state.showHeatmap}
                  onChange={e => update({ showHeatmap: e.target.checked })}
                />
                <span>Fitness Heatmap</span>
              </label>
            )}
            {isAnt && (
              <label className="xai-toggle">
                <input
                  type="checkbox"
                  checked={state.showPheromones}
                  onChange={e => update({ showPheromones: e.target.checked })}
                />
                <span>Pheromone Trails</span>
              </label>
            )}
            <label className="xai-toggle">
              <input
                type="checkbox"
                checked={state.showTopPerformers}
                onChange={e => update({ showTopPerformers: e.target.checked })}
              />
              <span>Top 5</span>
            </label>
            <label className="xai-toggle">
              <input
                type="checkbox"
                checked={state.showMetrics}
                onChange={e => update({ showMetrics: e.target.checked })}
              />
              <span>Diversity & Convergence</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TopControls;
