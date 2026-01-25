import React from 'react';

function GeneticControls({
  populationSize,
  generations,
  mutationRate,
  onPopulationChange,
  onGenerationsChange,
  onMutationRateChange,
}) {
  return (
    <div className="tuning">
      <label>
        <span>Population Size: {populationSize}</span>
        <input
          type="number"
          min="20"
          max="200"
          step="10"
          value={populationSize}
          onChange={e => onPopulationChange(Number(e.target.value))}
        />
      </label>
      <label>
        <span>Generations: {generations}</span>
        <input
          type="number"
          min="20"
          max="300"
          step="10"
          value={generations}
          onChange={e => onGenerationsChange(Number(e.target.value))}
        />
      </label>
      <label>
        <span>Mutation Rate: {(mutationRate * 100).toFixed(1)}%</span>
        <input
          type="range"
          min="0.01"
          max="0.2"
          step="0.01"
          value={mutationRate}
          onChange={e => onMutationRateChange(Number(e.target.value))}
        />
        <small style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
          Higher = more exploration
        </small>
      </label>
    </div>
  );
}

export default GeneticControls;
