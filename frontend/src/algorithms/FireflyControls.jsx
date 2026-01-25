import React from 'react';

function FireflyControls({
  fireflies = 60,
  absorption = 1.0,
  iterations = 200,
  randomness = 0.2,
  onFirefliesChange,
  onAbsorptionChange,
  onIterationsChange,
  onRandomnessChange
}) {
  return (
    <div className="tuning">
      <label>
        <span>Fireflies: {fireflies}</span>
        <input
          type="number"
          min="20"
          max="200"
          step="10"
          value={fireflies}
          onChange={e => onFirefliesChange?.(Number(e.target.value))}
        />
      </label>
      <label>
        <span>Absorption (γ): {absorption.toFixed(2)}</span>
        <input
          type="range"
          min="0.1"
          max="5.0"
          step="0.1"
          value={absorption}
          onChange={e => onAbsorptionChange?.(Number(e.target.value))}
        />
        <small style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
          Higher = shorter attraction range
        </small>
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
        <span>Randomness: {(randomness * 100).toFixed(0)}%</span>
        <input
          type="range"
          min="0"
          max="0.5"
          step="0.05"
          value={randomness}
          onChange={e => onRandomnessChange?.(Number(e.target.value))}
        />
        <small style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
          Higher = more exploration
        </small>
      </label>
    </div>
  );
}

export default FireflyControls;
