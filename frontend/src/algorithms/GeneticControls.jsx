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
      <h3>Genetic Algorithm</h3>
      <label>
        Population size
        <input
          type="number"
          min="10"
          step="5"
          value={populationSize}
          onChange={(event) => onPopulationChange(Number(event.target.value))}
        />
      </label>
      <label>
        Generations
        <input
          type="number"
          min="1"
          step="10"
          value={generations}
          onChange={(event) => onGenerationsChange(Number(event.target.value))}
        />
      </label>
      <label>
        Mutation rate
        <input
          type="number"
          min="0.01"
          max="1"
          step="0.01"
          value={mutationRate}
          onChange={(event) => onMutationRateChange(Number(event.target.value))}
        />
      </label>
    </div>
  );
}

export default GeneticControls;
