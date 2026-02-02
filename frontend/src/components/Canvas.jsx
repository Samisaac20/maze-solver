import React, { useRef, useEffect } from 'react';
import { drawMaze as drawMazeOnCanvas } from '../mazeRenderer';

function Canvas({ state }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const frame = state.history[Math.min(state.currentStep, state.history.length - 1)];
    const fallbackCandidates = state.solution?.final_candidates ?? [];
    const explorers = frame?.candidates ?? fallbackCandidates;
    const frameBest = frame?.best ?? state.solution?.best_candidate ?? null;
    const bestPath = frameBest?.path ?? state.solution?.path ?? [];
    const pheromoneMap = frame?.pheromone_map ?? null;

    drawMazeOnCanvas({
      canvas: canvasRef.current,
      maze: state.maze,
      explorers,
      bestPath,
      solution: state.solution,
      frameProgress: state.frameProgress,
      isRunning: state.isRunning,
      algorithmType: state.algorithm,
      showVelocities: state.showVelocities,
      showHeatmap: state.showHeatmap,
      showTopPerformers: state.showTopPerformers,
      showPheromones: state.showPheromones,
      pheromoneMap: pheromoneMap,
    });
  }, [
    state.maze,
    state.history,
    state.currentStep,
    state.solution,
    state.frameProgress,
    state.isRunning,
    state.algorithm,
    state.showVelocities,
    state.showHeatmap,
    state.showTopPerformers,
    state.showMetrics,
    state.showPheromones,
  ]);

  return (
    <section className="visuals">
      <canvas ref={canvasRef} />
    </section>
  );
}

export default Canvas;
