function PsoControls({ iterations, swarmSize, onIterationsChange, onSwarmSizeChange }) {
  return (
    <div className="tuning">
      <h3>PSO Tuning</h3>
      <label>
        Iterations
        <input
          type="number"
          min="1"
          step="1"
          value={iterations}
          onChange={(event) => onIterationsChange(Number(event.target.value))}
        />
      </label>
      <label>
        Swarm size
        <input
          type="number"
          min="1"
          step="1"
          value={swarmSize}
          onChange={(event) => onSwarmSizeChange(Number(event.target.value))}
        />
      </label>
    </div>
  );
}

export default PsoControls;
