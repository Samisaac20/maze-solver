import { useEffect } from 'react';
import './App.css';
import { useMazeSolver } from './hooks/useMazeSolver';
import { usePlayback } from './hooks/usePlayback';
import TopControls from './components/TopControls';
import Canvas from './components/Canvas';
import Sidebar from './components/Sidebar';

function App() {
  const { state, update, resetPlayback, fetchMaze, runSolver, handleReset } = useMazeSolver();

  // Playback animation
  usePlayback(state.isRunning, state.history.length, state.speedMs, (updates) => {
    update(typeof updates === 'function' ? updates(state) : updates);
  });

  // Auto-fetch maze on size or complexity change
  useEffect(() => {
    resetPlayback();
    const { desiredSize } = state;
    if (desiredSize >= 15 && desiredSize <= 100 && desiredSize % 5 === 0) {
      fetchMaze(desiredSize);
    }
  }, [state.desiredSize, state.selectedPreset, fetchMaze, resetPlayback]);

  // Clear solution on algorithm change
  useEffect(() => {
    resetPlayback();
    update({ solution: null, error: '', runFailed: false });
  }, [state.algorithm, resetPlayback, update]);

  return (
    <div className="app">
      <header>
        <h1>Maze Solver Visualiser with XAI</h1>
        <p>Explainable AI visualization of evolutionary algorithms</p>
      </header>

      <div className="main-content">
        <div className="left-column">
          <TopControls
            state={state}
            update={update}
            runSolver={runSolver}
            fetchMaze={fetchMaze}
            handleReset={handleReset}
          />
          <Sidebar state={state} update={update} />
        </div>
        <div className="right-column">
          <Canvas state={state} />
        </div>
      </div>
    </div>
  );
}

export default App;
