function PsoControls({
  iterations,
  swarmSize,
  iterationsPlaceholder,
  swarmPlaceholder,
  onIterationsChange,
  onSwarmSizeChange,
}) {
  return (
    <div className="tuning">
      <h3>PSO Tuning</h3>
      <label>
        Iterations
        <input
          type="number"
          min="1"
          step="1"
          value={iterations ?? ''}
          placeholder={iterationsPlaceholder}
          inputMode="numeric"
          onChange={(event) => {
            const { value } = event.target;
            onIterationsChange(value === '' ? null : Number(value));
          }}
        />
      </label>
      <label>
        Swarm size
        <input
          type="number"
          min="1"
          step="1"
          value={swarmSize ?? ''}
          placeholder={swarmPlaceholder}
          inputMode="numeric"
          onChange={(event) => {
            const { value } = event.target;
            onSwarmSizeChange(value === '' ? null : Number(value));
          }}
        />
      </label>
    </div>
  );
}

export default PsoControls;
