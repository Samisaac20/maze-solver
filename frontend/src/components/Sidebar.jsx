import React from 'react';
import PsoControls from '../algorithms/PsoControls';
import GeneticControls from '../algorithms/GeneticControls';
import FireflyControls from '../algorithms/FireflyControls';
import AntColonyControls from '../algorithms/AntColonyControls';

const ALGORITHMS = [
  { id: 'pso', label: 'Particle Swarm', name: 'Particle Swarm Optimization' },
  { id: 'genetic', label: 'Genetic Algorithm', name: 'Genetic Algorithm' },
  { id: 'firefly', label: 'Firefly Algorithm', name: 'Firefly Algorithm' },
  { id: 'ant', label: 'Ant Colony', name: 'Ant Colony Optimization' },
];

const EXPLANATIONS = {
  pso: [
    'Launch a swarm of explorers from the maze entrance.',
    'Each explorer remembers its best position while the swarm tracks the global best route.',
    'They drift toward both memories with a nudge of randomness to stay curious.',
    'The best path emerges where most explorers consistently converge.',
  ],
  genetic: [
    'Generate a population of complete maze routes, even if many are rough.',
    'Score every route by distance, coverage, and efficiency.',
    'Keep the fittest, mix them, and mutate small sections to produce new paths.',
    'Repeat until one offspring reaches the exit.',
  ],
  firefly: [
    'Each firefly represents a potential solution, glowing brighter when closer to the goal.',
    'Dimmer fireflies are attracted to and move toward brighter ones nearby.',
    'Light intensity fades with distance (absorption), limiting attraction range.',
    'Random movements prevent premature convergence, the brightest path wins.',
  ],
  ant: [
    'Send simulated ants through the maze while they drop pheromones on good tiles.',
    'Shorter or more promising paths collect stronger pheromone trails.',
    'Bolder trails attract later ants, reinforcing useful passages.',
    'Eventually the pheromone map reveals a continuous route to the exit.',
  ],
};

// Helper function to calculate diversity (spread of population)
const calculateDiversity = (explorers, maze) => {
  if (!explorers || explorers.length < 2) return 0;
  
  const positions = explorers.map(e => {
    if (e.position) return e.position;
    if (e.path && e.path.length > 0) return e.path[e.path.length - 1];
    return null;
  }).filter(p => p !== null);
  
  if (positions.length < 2) return 0;
  
  let totalDistance = 0;
  let comparisons = 0;
  
  for (let i = 0; i < positions.length; i++) {
    for (let j = i + 1; j < positions.length; j++) {
      const [r1, c1] = positions[i];
      const [r2, c2] = positions[j];
      const distance = Math.sqrt(Math.pow(r1 - r2, 2) + Math.pow(c1 - c2, 2));
      totalDistance += distance;
      comparisons++;
    }
  }
  
  const mazeSize = Math.sqrt(maze.length * (maze[0]?.length || 1));
  return comparisons > 0 ? (totalDistance / comparisons) / mazeSize : 0;
};

// Helper function to calculate convergence (clustering around best)
const calculateConvergence = (explorers, bestCandidate) => {
  if (!explorers || explorers.length < 2 || !bestCandidate) return 0;
  
  const bestPos = bestCandidate.position || 
                 (bestCandidate.path && bestCandidate.path.length > 0 ? 
                  bestCandidate.path[bestCandidate.path.length - 1] : null);
  
  if (!bestPos) return 0;
  
  let totalDistance = 0;
  let count = 0;
  
  explorers.forEach(e => {
    const pos = e.position || (e.path && e.path.length > 0 ? e.path[e.path.length - 1] : null);
    if (pos) {
      const distance = Math.sqrt(
        Math.pow(pos[0] - bestPos[0], 2) + 
        Math.pow(pos[1] - bestPos[1], 2)
      );
      totalDistance += distance;
      count++;
    }
  });
  
  const avgDistance = count > 0 ? totalDistance / count : 0;
  return 1 / (1 + avgDistance);
};

function Sidebar({ state, update }) {
  const { algorithm, mazeSize, history, solution, mazeAnalysis } = state;

  const algo = ALGORITHMS.find(a => a.id === algorithm);
  const isGenetic = algorithm === 'genetic';
  const isPso = algorithm === 'pso';
  const isFirefly = algorithm === 'firefly';
  const isAnt = algorithm === 'ant';

  const sizeLabel = mazeSize ?? (state.maze.length ?
    `${state.maze.length} x ${state.maze[0].length}` : '-');

  const frame = history[state.currentStep];
  const explorers = frame?.candidates ?? solution?.final_candidates ?? [];

  let trackedCount = explorers.length;
  if (!trackedCount) {
    if (isGenetic) trackedCount = solution?.population_size || '-';
    else if (isPso) trackedCount = solution?.swarm_size || '-';
    else if (isFirefly) trackedCount = solution?.fireflies || '-';
    else if (isAnt) trackedCount = solution?.ants || '-';
    else trackedCount = '-';
  }

  const currentFrameLabel = history.length ?
    `${isGenetic ? 'Generation' : 'Iteration'} ${Math.min(state.currentStep + 1, history.length)}/${history.length}` : '-';

  const frameBest = frame?.best ?? solution?.best_candidate ?? null;
  const fitness = frameBest?.fitness ?? solution?.best_fitness ?? null;
  const bestFitness = typeof fitness === 'number' ? fitness.toFixed(2) : '-';

  const explorationCoverage = explorers.length > 0 ? (() => {
    const visited = new Set();
    explorers.forEach(e => {
      if (e.path) e.path.forEach(([r, c]) => visited.add(`${r},${c}`));
    });
    return ((visited.size / (state.maze.length * (state.maze[0]?.length || 1))) * 100).toFixed(1);
  })() : '-';

  // Try to get metrics from backend data
  let diversityMetric = frame?.diversity ?? 
                         frame?.metrics?.diversity ?? 
                         solution?.diversity ?? 
                         solution?.metrics?.diversity ?? 
                         null;
  
  let convergenceMetric = frame?.convergence ?? 
                           frame?.metrics?.convergence ?? 
                           solution?.convergence ?? 
                           solution?.metrics?.convergence ?? 
                           null;
  
  // If metrics not provided by backend, calculate them client-side
  if (diversityMetric === null && explorers.length > 0 && state.maze.length > 0) {
    diversityMetric = calculateDiversity(explorers, state.maze);
  }
  
  if (convergenceMetric === null && explorers.length > 0 && frameBest) {
    convergenceMetric = calculateConvergence(explorers, frameBest);
  }
  
  const diversity = typeof diversityMetric === 'number' ? diversityMetric.toFixed(3) : '-';
  const convergence = typeof convergenceMetric === 'number' ? convergenceMetric.toFixed(3) : '-';

  const algorithmControls = (() => {
    switch (algorithm) {
      case 'pso':
        return <PsoControls
          iterations={state.iterations}
          swarmSize={state.swarmSize}
          iterationsPlaceholder={240}
          swarmPlaceholder={70}
          onIterationsChange={v => update({ iterations: v })}
          onSwarmSizeChange={v => update({ swarmSize: v })}
        />;
      case 'genetic':
        return <GeneticControls
          populationSize={state.gaPopulation}
          generations={state.gaGenerations}
          mutationRate={state.gaMutationRate}
          onPopulationChange={v => update({ gaPopulation: v })}
          onGenerationsChange={v => update({ gaGenerations: v })}
          onMutationRateChange={v => update({ gaMutationRate: v })}
        />;
      case 'firefly':
        return <FireflyControls
          fireflies={state.fireflyCount}
          absorption={state.fireflyAbsorption}
          iterations={state.fireflyIterations}
          randomness={state.fireflyRandomness}
          onFirefliesChange={v => update({ fireflyCount: v })}
          onAbsorptionChange={v => update({ fireflyAbsorption: v })}
          onIterationsChange={v => update({ fireflyIterations: v })}
          onRandomnessChange={v => update({ fireflyRandomness: v })}
        />;
      case 'ant':
        return <AntColonyControls
          ants={state.antCount}
          iterations={state.antIterations}
          evaporationRate={state.antEvaporationRate}
          alpha={state.antAlpha}
          beta={state.antBeta}
          onAntsChange={v => update({ antCount: v })}
          onIterationsChange={v => update({ antIterations: v })}
          onEvaporationRateChange={v => update({ antEvaporationRate: v })}
          onAlphaChange={v => update({ antAlpha: v })}
          onBetaChange={v => update({ antBeta: v })}
        />;
      default:
        return null;
    }
  })();

  return (
    <>
      {/* 1. HOW IT WORKS - TOP */}
      {EXPLANATIONS[algorithm] && (
        <div className="sidebar-section">
          <h2>How This Works</h2>
          <ul>
            {EXPLANATIONS[algorithm].map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
      )}

      {/* 2. PARAMETERS - BELOW HOW IT WORKS */}
      <div className="sidebar-section">
        <h2>Algorithm Parameters</h2>
        {algorithmControls}
      </div>

      {/* 3. PLAYBACK DETAILS - BELOW PARAMETERS */}
      <div className="sidebar-section">
        <h2>Playback Details</h2>
        <ul>
          <li>Algorithm: {algo?.name}</li>
          <li>Maze: {sizeLabel}</li>
          <li>{isGenetic ? 'Population' : isFirefly ? 'Fireflies' : isAnt ? 'Ants' : 'Particles'}: {trackedCount}</li>
          <li>{isGenetic ? 'Generations' : 'Iterations'}: {history.length}</li>
          <li>Frame: {currentFrameLabel}</li>
          <li>Fitness: {bestFitness}</li>
          <li>Coverage: {explorationCoverage}%</li>
          <li>Diversity: {diversity}</li>
          <li>Convergence: {convergence}</li>
        </ul>
      </div>

      {/* 4. MAZE ANALYSIS - BELOW PLAYBACK */}
      {mazeAnalysis && (
        <div className="sidebar-section">
          <h2>Maze Analysis</h2>
          <ul>
            <li>Junctions: {mazeAnalysis.junctions}</li>
            <li>Dead ends: {mazeAnalysis.dead_ends}</li>
            <li>Openness: {(mazeAnalysis.openness * 100).toFixed(1)}%</li>
            <li>Decisions: {mazeAnalysis.decisions_per_100_cells.toFixed(1)}/100</li>
          </ul>
        </div>
      )}

      {/* 5. XAI INSIGHTS - BOTTOM */}
      {solution && (
        <div className="sidebar-section">
          <h2>XAI Insights</h2>
          <ul>
            <li>Status: {solution.solved ? '✓ Solved' : '✗ Incomplete'}</li>
            {solution.path && (
              <li>Path: {solution.path.length} steps</li>
            )}
            {isPso && explorers.length > 0 && (
              <li>Avg Velocity: {
                (explorers.reduce((sum, e) => {
                  if (!e.velocity) return sum;
                  const [vx, vy] = e.velocity;
                  return sum + Math.sqrt(vx * vx + vy * vy);
                }, 0) / explorers.length).toFixed(3)
              }</li>
            )}
            {isGenetic && (
              <>
                <li>Mutation: {(state.gaMutationRate * 100).toFixed(1)}%</li>
                <li>Elite: {Math.max(1, Math.floor(state.gaPopulation / 10))}</li>
              </>
            )}
            {isFirefly && explorers.length > 0 && (
              <>
                <li>Avg Brightness: {
                  (explorers.reduce((sum, e) => sum + (e.brightness || 0), 0) / explorers.length).toFixed(3)
                }</li>
                <li>Max Brightness: {
                  Math.max(...explorers.map(e => e.brightness || 0)).toFixed(3)
                }</li>
              </>
            )}
            {isAnt && explorers.length > 0 && (
              <>
                <li>Avg Pheromone: {
                  (explorers.reduce((sum, e) => sum + (e.pheromone_strength || 0), 0) / explorers.length).toFixed(3)
                }</li>
                <li>Max Pheromone: {
                  Math.max(...explorers.map(e => e.pheromone_strength || 0)).toFixed(3)
                }</li>
                <li>Successful: {
                  explorers.filter(e => e.solved).length
                }/{explorers.length}</li>
              </>
            )}
          </ul>
        </div>
      )}
    </>
  );
}

export default Sidebar;
