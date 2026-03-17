# Maze Solver Visualiser with XAI

An interactive web application for visualising and comparing evolutionary algorithms solving maze path finding problems. Features real-time algorithm execution with explainable AI (XAI) overlays to understand how different optimisation strategies explore and converge on solutions.

# Project Overview

This project is a dissertation work focused on **Explainable AI (XAI) for Evolutionary Algorithms**. It provides real-time visualisation of four different evolutionary algorithms solving maze path finding problems:

- **Particle Swarm Optimisation (PSO)** - Swarm intelligence with velocity vectors
- **Genetic Algorithm (GA)** - Evolution through selection, crossover, and mutation
- **Firefly Algorithm (FA)** - Bio-inspired optimisation with attraction mechanics
- **Ant Colony Optimisation (ACO)** - Pheromone-based path finding

### Key Features

#### Algorithm Visualisation

- Real-time streaming visualisation
- Frame-by-frame playback with adjustable speed
- Colour-coded trails (Green = successful, Red = failed)
- Live algorithm state updates

#### XAI (Explainable AI) Features

- Diversity metrics - population spread visualisation
- Convergence tracking - clustering around solutions
- Top performer highlighting - identify best candidates
- Velocity vectors (PSO) - show particle movement direction
- Fitness heat-maps (GA) - cell-level exploration intensity
- Pheromone trails (ACO) - chemical trail visualisation

#### Maze Generation

- Configurable complexity levels (Trivial → Extreme)
- Size range: 15x15 to 100x100 (5-step increments)
- Maze analysis metrics (junctions, dead ends, openness)
- Perfect maze generation (guaranteed solvable)

#### Customisation

- Algorithm-specific parameter tuning
- Modern dark theme with neon accents
- Responsive design with optimal layout
- Modern custom scrollbar

## Getting Started

### Prerequisites

- **Node.js** (v16 or higher)
- **Python** 3.9+ (for backend)
- **npm**
- **Git**

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Samisaac20/maze-solver.git
cd maze-solver
```

#### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

#### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

### Start the Backend

```bash
cd backend
venv\Scripts\activate # or source venv/bin/activate on Linux

# Run FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Start the Frontend

```bash
cd frontend
npm run dev
```

The application will open at `http://localhost:5173` (or next available port)

## Project Structure

```bash
maze-solver/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Canvas.jsx        # Maze visualisation canvas
│   │   │   ├── Sidebar.jsx       # Algorithm info & metrics
│   │   │   └── TopControls.jsx   # Algorithm & maze controls
│   │   ├── algorithms/
│   │   │   ├── PsoControls.jsx
│   │   │   ├── GeneticControls.jsx
│   │   │   ├── FireflyControls.jsx
│   │   │   └── AntColonyControls.jsx
│   │   ├── hooks/
│   │   │   ├── useMazeSolver.js  # State management
│   │   │   └── usePlayback.js    # Animation controller
│   │   ├── index.css
│   │   ├── App.jsx               # Main application component
│   │   ├── mazeRenderer.js       # Canvas drawing logic
│   │   ├── App.css               # Global styles
│   │   └── main.jsx              # Entry point
│   ├── package.json
│   ├── vite.config.js
│   └── .gitignore
│
├── backend/
│   ├── app/
│   │   ├── algorithms/
│   │   │   ├── pso/
│   │   │   │   └──pso_solver.py                # Particle Swarm
│   │   │   ├── genetic/
│   │   │   │   └── genetic_solver.py           # Genetic Algorithm
│   │   │   ├── firefly/
│   │   │   │   └── firefly_solver.py           # Firefly Algorithm
│   │   │   ├── ant_colony/
│   │   │   │   └── ant_colony_solver.py        # Ant Colony
│   │   ├── maze_logic/
│   │   │   └── maze_gen.py                     # Maze generation
│   ├── main.py                                 # FastAPI application
│   └── requirements.txt
│
├── README.md                     # This file
└── .gitignore
```
