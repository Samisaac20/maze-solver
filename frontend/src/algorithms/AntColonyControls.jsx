import React from 'react';

function AntColonyControls({
  ants = 60,
  iterations = 150,
  evaporationRate = 0.5,
  alpha = 1.0,
  beta = 2.0,
  onAntsChange,
  onIterationsChange,
  onEvaporationRateChange,
  onAlphaChange,
  onBetaChange
}) {
  return (
    <div className="tuning">
      <label>
        <span>Ants: {ants}</span>
        <input
          type="number"
          min="20"
          max="200"
          step="10"
          value={ants}
          onChange={e => onAntsChange?.(Number(e.target.value))}
        />
      </label>
      <label>
        <span>Iterations: {iterations}</span>
        <input
          type="number"
          min="50"
          max="500"
          step="10"
          value={iterations}
          onChange={e => onIterationsChange?.(Number(e.target.value))}
        />
      </label>
      <label>
        <span>Evaporation Rate: {(evaporationRate * 100).toFixed(0)}%</span>
        <input
          type="range"
          min="0.1"
          max="0.9"
          step="0.05"
          value={evaporationRate}
          onChange={e => onEvaporationRateChange?.(Number(e.target.value))}
        />
        <small style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
          Higher = trails fade faster
        </small>
      </label>
      <label>
        <span>Alpha (α - Pheromone): {alpha.toFixed(1)}</span>
        <input
          type="range"
          min="0.5"
          max="5.0"
          step="0.1"
          value={alpha}
          onChange={e => onAlphaChange?.(Number(e.target.value))}
        />
        <small style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
          Higher = follow trails more
        </small>
      </label>
      <label>
        <span>Beta (β - Heuristic): {beta.toFixed(1)}</span>
        <input
          type="range"
          min="0.5"
          max="5.0"
          step="0.1"
          value={beta}
          onChange={e => onBetaChange?.(Number(e.target.value))}
        />
        <small style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
          Higher = follow goal direction more
        </small>
      </label>
    </div>
  );
}

export default AntColonyControls;
