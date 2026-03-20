<p align="center">
  <h1 align="center">🏎️ NASCAR AI Strategy Engine</h1>
  <p align="center">
    <strong>Data-driven pit stop optimization powered by physics simulation, machine learning, and Monte Carlo analysis</strong>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#dashboard">Dashboard</a> •
    <a href="#api-usage">API Usage</a> •
    <a href="#documentation">Docs</a>
  </p>
</p>

---

## Overview

The **NASCAR AI Strategy Engine** is a comprehensive race strategy optimization framework that combines physics-based simulation, XGBoost caution prediction, Monte Carlo evaluation, and sensitivity analysis to help teams make smarter pit stop decisions.

Instead of relying solely on intuition and experience, this engine quantifies the risk and reward of every strategic option — evaluating hundreds of simulated race scenarios in seconds to recommend optimal pit timing with statistical confidence.

---

## Features

| Module | Description |
|--------|-------------|
| **Physics Simulator** | Lap-time decomposition model with tire degradation, fuel weight, traffic (dirty air), and caution dynamics |
| **Caution Predictor** | XGBoost classifier trained on 18 engineered features — Validation AUC: **0.80** |
| **Monte Carlo Engine** | Parallel evaluation of strategies across 200+ simulated races in under 4 seconds |
| **Sensitivity Analyzer** | Grid search + `scipy.optimize` to find optimal pit windows with position-level precision |
| **Interactive Dashboard** | Streamlit web app with real-time strategy comparison, optimization, and live simulation |

### Performance

| Component | Target | Actual |
|-----------|--------|--------|
| Single race simulation (100 laps) | < 5 s | **0.037 s** |
| Monte Carlo evaluation (200 sims) | < 30 s | **3.6 s** |
| Sensitivity analysis | < 5 s | **0.5 s** |
| End-to-end workflow | < 30 s | **2.8 s** |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate synthetic training data

```bash
python data/generate_synthetic_data.py
```

### 3. Train the caution prediction model

```bash
python train_caution_model.py
```

### 4. Launch the interactive dashboard

```bash
./run_dashboard.sh
# or
streamlit run app.py
```

The dashboard opens at **http://localhost:8501** with four tabs:

- **Strategy Comparison** — side-by-side Monte Carlo evaluation of preset and custom strategies
- **Sensitivity Analysis** — pit timing sensitivity curves with optimal window identification
- **Strategy Optimizer** — one-click automatic optimization of pit stop laps
- **Live Simulation** — watch a race unfold lap by lap with real-time position tracking

---

## Architecture

```
NASCAR-AI-Strategy-Engine/
│
├── src/                        # Core engine
│   ├── simulator.py            # Physics-based race simulator
│   ├── features.py             # Feature engineering for caution prediction
│   ├── models.py               # XGBoost caution prediction model
│   ├── strategy.py             # Strategy & pit stop definitions
│   ├── monte_carlo.py          # Parallel Monte Carlo evaluator
│   └── sensitivity.py          # Sensitivity analysis & optimization
│
├── tests/                      # Test suite (83 tests, 100% pass rate)
│   ├── test_simulator.py       # 28 unit tests
│   ├── test_models.py          # 15 unit tests
│   ├── test_monte_carlo.py     # 14 unit tests
│   ├── test_sensitivity.py     # 13 unit tests
│   └── test_integration.py     # 13 integration tests
│
├── data/                       # Data generation & storage
│   └── generate_synthetic_data.py
│
├── models/                     # Trained model artifacts
│
├── docs/                       # Documentation & business materials
│   ├── BUSINESS_CASE.md        # ROI analysis for team adoption
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── DEMO_SCRIPT.md
│   └── phases/                 # Development phase summaries
│
├── app.py                      # Streamlit dashboard
├── config.py                   # Centralized configuration
├── benchmark.py                # Performance benchmarks
├── demo_monte_carlo.py         # Quick demo script
├── train_caution_model.py      # Model training script
├── run_dashboard.sh            # Dashboard launcher
└── requirements.txt            # Python dependencies
```

---

## API Usage

### Compare strategies with Monte Carlo

```python
from src.monte_carlo import MonteCarloEvaluator
from src.strategy import PRESET_STRATEGIES

evaluator = MonteCarloEvaluator(
    sim_config={'num_cars': 40, 'num_laps': 200},
    n_jobs=-1  # use all CPU cores
)

comparison, results = evaluator.compare_strategies(
    PRESET_STRATEGIES,
    num_simulations=200
)
print(comparison)
```

### Optimize pit stop timing

```python
from src.sensitivity import StrategySensitivityAnalyzer

analyzer = StrategySensitivityAnalyzer(evaluator)
optimized_strategy = analyzer.optimize_complete_strategy(
    PRESET_STRATEGIES['standard'],
    search_ranges=[(35, 65), (85, 115), (135, 165)]
)
```

### Run a single simulation

```python
from src.simulator import RaceSimulator

sim = RaceSimulator(num_cars=40, num_laps=200, random_seed=42)
result = sim.simulate_race()
print(f"Winner: Car #{result['winner']}")
```

### Predict caution probability

```python
from src.models import CautionPredictor

predictor = CautionPredictor()
predictor.load('models/caution_predictor.pkl')

prob = predictor.predict_caution_probability({
    'race_progress': 0.75,
    'laps_since_last_caution': 30,
    'avg_tire_age': 40.0,
    'green_flag_run_length': 30,
    'caution_density': 0.08
})
print(f"Caution probability: {prob:.1%}")
```

---

## Preset Strategies

| Strategy | Description | Pit Stops |
|----------|-------------|-----------|
| **Standard** | Balanced 3-stop | Laps 50, 100, 150 |
| **Aggressive** | Early and frequent | Laps 40, 80, 120, 160 |
| **Conservative** | Late and minimal | Laps 60, 130 |
| **Two-Stop** | Fuel-focused | Laps 65, 135 |
| **Four-Stop** | Fresh tires priority | Laps 40, 80, 120, 160 |
| **Late Race Hero** | Track position gamble | Laps 45, 140 |

---

## Testing

```bash
# Run full test suite
python -m pytest tests/ -v

# Run benchmarks
python benchmark.py

# Run Monte Carlo demo
python demo_monte_carlo.py
```

**Test coverage:** 83/83 tests passing (100%)

---

## How It Works

### 1. Physics Simulation
The simulator models each lap as a composition of effects:

```
lap_time = base_time + tire_penalty + fuel_penalty + traffic_penalty + noise
```

- **Tire degradation** follows an exponential curve capped at 5.0 s
- **Fuel weight** decreases linearly, reducing lap time over a stint
- **Traffic (dirty air)** penalizes cars within 1.0 s of the car ahead
- **Caution periods** slow the entire field with realistic pacing

### 2. Caution Prediction
An XGBoost classifier predicts caution probability using 18 features:
- Race progress, green flag run length, caution history
- Field competitiveness (lap time variance, spread)
- Tire wear statistics across the field
- Position volatility

### 3. Monte Carlo Evaluation
Each strategy is evaluated across hundreds of stochastic simulations using `joblib` for parallel execution. Output metrics include:
- Mean finishing position
- Win rate, Top-5 rate, Top-10 rate
- Standard deviation (consistency)
- Statistical significance tests (t-test, Mann-Whitney U, Cohen's d)

### 4. Sensitivity Analysis
Grid search and `scipy.optimize.minimize_scalar` identify the optimal pit lap within a given window, quantifying how many positions are gained or lost by mistiming a stop.

---

## Dashboard

The Streamlit dashboard provides an interactive interface for the entire engine:

| Tab | Purpose |
|-----|---------|
| **Strategy Comparison** | Compare multiple strategies with Monte Carlo simulation results and Plotly charts |
| **Sensitivity Analysis** | Visualize how pit timing affects finishing position |
| **Strategy Optimizer** | Automatically find the best pit stop laps |
| **Live Simulation** | Watch a race unfold with real-time position updates |

Launch with:
```bash
streamlit run app.py
```

---

## Business Value

A 1–3 position improvement per race translates to **$100K–$500K in additional prize money per event**. See [`docs/BUSINESS_CASE.md`](docs/BUSINESS_CASE.md) for the full ROI analysis and [`docs/IMPLEMENTATION_ROADMAP.md`](docs/IMPLEMENTATION_ROADMAP.md) for the production deployment timeline.

---

## Tech Stack

- **Python 3.10+**
- **NumPy / Pandas / SciPy** — numerical computing
- **XGBoost / scikit-learn** — machine learning
- **Plotly / Streamlit** — visualization & dashboard
- **joblib** — parallel processing
- **pytest** — testing

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/BUSINESS_CASE.md`](docs/BUSINESS_CASE.md) | ROI analysis and team value proposition |
| [`docs/IMPLEMENTATION_ROADMAP.md`](docs/IMPLEMENTATION_ROADMAP.md) | Production deployment roadmap |
| [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) | Guided demo walkthrough |
| [`docs/PRESENTATION_SLIDES.md`](docs/PRESENTATION_SLIDES.md) | Presentation materials |
| [`docs/PROJECT_COMPLETE.md`](docs/PROJECT_COMPLETE.md) | Full project summary and metrics |

---

## License

This project is proprietary. All rights reserved.

---

<p align="center">
  Built for speed. Engineered for victory. 🏁
</p>
