import React from 'react';

function PsoControls({
  iterations,
  swarmSize,
  onIterationsChange,
  onSwarmSizeChange,
}) {
  return (
    <div className="tuning">
      <label>
        <span>Iterations: {iterations}</span>
        <input
          type="number"
          min="50"
          max="500"
          step="10"
          value={iterations}
          onChange={e => onIterationsChange(Number(e.target.value))}
        />
      </label>
      <label>
        <span>Swarm Size: {swarmSize}</span>
        <input
          type="number"
          min="20"
          max="200"
          step="10"
          value={swarmSize}
          onChange={e => onSwarmSizeChange(Number(e.target.value))}
        />
      </label>
    </div>
  );
}

export default PsoControls;
