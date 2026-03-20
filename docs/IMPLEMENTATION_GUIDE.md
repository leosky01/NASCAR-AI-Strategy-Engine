# Implementation Guide - NASCAR AI Strategy Engine

## 🎯 Execution Framework

Each phase follows: **DEVELOP → ANALYZE → CONTROL**

### DEVELOP
- Write code for the component
- Follow specifications exactly
- Include docstrings and type hints

### ANALYZE
- Test the component independently
- Verify outputs are reasonable
- Check edge cases

### CONTROL
- Run validation checks
- Document findings
- Sign off before next phase

---

## PHASE 1: PHYSICS-BASED SIMULATOR

### Overview
Replace random position logic with physically consistent model where lap times depend on tire age, fuel level, and traffic.

---

### 1.1 DEVELOP - Core Data Structures

**File**: `src/simulator.py`

**Tasks**:
1. Create `CarPhysics` dataclass (base_lap_time, tire_degradation_rate, etc.)
2. Create `CarState` dataclass (cumulative_time, tire_age, fuel_level, etc.)
3. Create `PitStop` dataclass
4. Create `RaceSimulator` class skeleton

**Expected Output**:
- Data structures defined
- Type hints included
- Docstrings for each class

**Validation**:
```python
# Check that classes can be instantiated
from src.simulator import CarPhysics, CarState, PitStop

physics = CarPhysics(base_lap_time=48.0)
state = CarState(car_id=0, physics=physics)
pit = PitStop(lap=50, duration=19.5)
```

---

### 1.2 DEVELOP - Lap Time Calculation

**File**: `src/simulator.py` (continued)

**Tasks**:
1. Implement `CarState.get_tire_penalty()` method
   - Use exponential degradation: `rate * age * (1 + exp(-age/20))`
2. Implement `CarState.get_fuel_penalty()` method
   - Linear: `fuel_weight * fuel_level`
3. Implement `CarState.get_noise()` method
   - Gaussian: `normal(0, 0.15 * consistency)`
4. Implement `RaceSimulator.calculate_lap_time()` method
   - Sum all components
   - Apply caution slowdown if active

**Expected Output**:
- Methods return realistic lap times (45-55 seconds)
- Old tires = slower times
- More fuel = slower times

**Validation**:
```python
# Test lap time calculation
sim = RaceSimulator()
sim.initialize_cars()

car = sim.cars[0]
lap_time = sim.calculate_lap_time(car)

assert 45 < lap_time < 55, f"Lap time {lap_time} out of range"

# Test tire degradation
car.tire_age = 0
new_tire_time = sim.calculate_lap_time(car)

car.tire_age = 50
old_tire_time = sim.calculate_lap_time(car)

assert old_tire_time > new_tire_time, "Old tires should be slower"
```

---

### 1.3 DEVELOP - Traffic Effects

**File**: `src/simulator.py` (continued)

**Tasks**:
1. Implement `RaceSimulator.calculate_traffic_penalty()` method
   - Find position in sorted times
   - Calculate gap to car ahead
   - Apply penalty if gap < 1.0 second
   - Modify by overtaking_ability

**Expected Output**:
- Cars in clean air (leader) get no penalty
- Cars close behind get penalty
- High overtaking ability reduces penalty

**Validation**:
```python
# Test traffic calculation
sim = RaceSimulator()
sim.initialize_cars()

sorted_times = [(0, 1000), (1, 1000.5), (2, 1001.5)]  # Car 1 is 0.5s behind

car = sim.cars[1]
penalty = sim.calculate_traffic_penalty(car, sorted_times)

assert penalty > 0, "Should have traffic penalty"
assert penalty < 1.0, f"Penalty {penalty} too large"
```

---

### 1.4 DEVELOP - Race Simulation Loop

**File**: `src/simulator.py` (continued)

**Tasks**:
1. Implement `RaceSimulator.simulate_lap()` method
   - Handle pit stops
   - Calculate lap times for all cars
   - Update cumulative times
   - Update positions by sorting
   - Update tire age and fuel

2. Implement `RaceSimulator.simulate_race()` method
   - Initialize cars
   - Loop through all laps
   - Return final results

**Expected Output**:
- Complete race simulation
- All cars have unique final positions (1-40)
- Cumulative times are monotonically increasing

**Validation**:
```python
# Test full race
sim = RaceSimulator(num_cars=40, num_laps=200)
result = sim.simulate_race()

# Check positions
positions = list(result['final_positions'].values())
assert len(set(positions)) == 40, "Positions not unique"
assert set(positions) == set(range(1, 41)), "Missing positions"

# Check times
times = list(result['final_times'].values())
assert all(t > 0 for t in times), "Invalid times"
```

---

### 1.5 ANALYZE - Physics Validation

**File**: `tests/test_simulator.py`

**Tasks**:
1. Create test suite
2. Test lap time ranges
3. Test tire degradation curve
4. Test fuel weight effect
5. Test traffic penalty
6. Test full race

**Expected Output**:
- All tests pass
- Lap times in realistic range
- Tire degradation shows acceleration
- Fuel effect is linear
- Traffic affects appropriately

**Validation**:
```bash
pytest tests/test_simulator.py -v
```

---

### 1.6 CONTROL - Sign-off Checklist

**Verify**:
- [ ] Simulator runs 200-lap race in < 5 seconds
- [ ] Lap times are 45-55 seconds
- [ ] Tire degradation increases with age
- [ ] Fuel weight affects lap time
- [ ] Positions determined by cumulative time (not random)
- [ ] Pit stops add ~20 seconds
- [ ] All tests pass

**Metrics to Record**:
- Average lap time: ___ seconds
- Tire degradation (0 vs 50 laps): ___ seconds difference
- Fuel effect (100% vs 0%): ___ seconds difference
- 200-lap race time: ___ seconds

**Next Phase**: Caution Prediction Model

---

## PHASE 2: CAUTION PREDICTION MODEL

### Overview
Upgrade from Logistic Regression to XGBoost with engineered features.

---

### 2.1 DEVELOP - Feature Engineering

**File**: `src/features.py`

**Tasks**:
1. Implement `extract_caution_features()` function
   - Race context (progress, laps remaining)
   - Caution history (cautions so far, laps since last)
   - Field competitiveness (lap time variance)
   - Tire wear statistics
   - Position volatility

2. Implement `prepare_training_data()` function
   - Extract features for each lap
   - Label: caution in next 5 laps?
   - Return X, y, feature_names

**Expected Output**:
- 15+ engineered features
- Feature names documented
- Handles early laps (no history)

**Validation**:
```python
# Test feature extraction
df = pd.read_csv('data/race_data.csv')
features = extract_caution_features(df, lap=100)

assert 'race_progress' in features
assert 'laps_since_last_caution' in features
assert 0 <= features['race_progress'] <= 1
```

---

### 2.2 DEVELOP - XGBoost Model

**File**: `src/models.py`

**Tasks**:
1. Create `CautionPredictor` class
   - Initialize XGBClassifier with balanced params
2. Implement `train()` method
   - Train/test split
   - Fit model
   - Calculate metrics (AUC, feature importance)
3. Implement `predict_caution_probability()` method
   - Return probability (0-1)

**Expected Output**:
- Model trains successfully
- AUC > 0.65 (better than random)
- Feature importance available

**Validation**:
```python
# Test model
predictor = CautionPredictor()
metrics = predictor.train(X, y, feature_names)

assert metrics['val_auc'] > 0.6, "Model not learning"
assert 'feature_importance' in metrics
```

---

### 2.3 ANALYZE - Model Evaluation

**File**: `tests/test_models.py`

**Tasks**:
1. Test feature extraction
2. Test model training
3. Test prediction
4. Analyze feature importance
5. Plot ROC curve (optional)

**Expected Output**:
- All tests pass
- Top features make sense (race_progress, laps_since_caution)
- Model generalizes to validation set

**Validation**:
```bash
pytest tests/test_models.py -v
```

---

### 2.4 CONTROL - Sign-off Checklist

**Verify**:
- [ ] Model trains in < 30 seconds
- [ ] Validation AUC > 0.65
- [ ] Features are interpretable
- [ ] Prediction returns probability 0-1
- [ ] Model can be saved/loaded
- [ ] All tests pass

**Metrics to Record**:
- Training AUC: ___
- Validation AUC: ___
- Top 3 features: ___
- Inference time: ___ ms

**Next Phase**: Monte Carlo Engine

---

## PHASE 3: MONTE CARLO ENGINE

### Overview
Parallelize strategy evaluation for faster, more robust analysis.

---

### 3.1 DEVELOP - Single Simulation Function

**File**: `src/monte_carlo.py`

**Tasks**:
1. Implement `run_single_simulation()` function
   - Create simulator with seed
   - Run race with strategy
   - Return results (position, time, winner)

**Expected Output**:
- Deterministic given seed
- Returns consistent results structure

**Validation**:
```python
# Test reproducibility
result1 = run_single_simulation(config, strategy, seed=42)
result2 = run_single_simulation(config, strategy, seed=42)

assert result1['position'] == result2['position']
```

---

### 3.2 DEVELOP - Parallel Evaluator

**File**: `src/monte_carlo.py` (continued)

**Tasks**:
1. Create `MonteCarloEvaluator` class
2. Implement `evaluate_strategy()` method
   - Use joblib.Parallel
   - Run N simulations with different seeds
   - Return statistics (mean, std, win_rate, etc.)

3. Implement `compare_strategies()` method
   - Evaluate multiple strategies
   - Return comparison DataFrame

**Expected Output**:
- 200 simulations run in < 30 seconds
- Returns distribution metrics
- Handles all preset strategies

**Validation**:
```python
# Test parallel execution
evaluator = MonteCarloEvaluator(config, n_jobs=2)
results = evaluator.evaluate_strategy(strategy, num_simulations=50)

assert 'mean_position' in results
assert 'win_rate' in results
assert len(results['positions']) == 50
```

---

### 3.3 ANALYZE - Performance & Correctness

**File**: `tests/test_monte_carlo.py`

**Tasks**:
1. Test single simulation
2. Test parallel execution
3. Test reproducibility (same seed = same result)
4. Test statistics calculation
5. Benchmark performance

**Expected Output**:
- All tests pass
- Speedup from parallelization
- Results are reproducible

**Validation**:
```bash
pytest tests/test_monte_carlo.py -v
```

---

### 3.4 CONTROL - Sign-off Checklist

**Verify**:
- [ ] 200 simulations complete in < 30 seconds
- [ ] Results are reproducible with same seed
- [ ] Statistics are calculated correctly
- [ ] Multiple strategies can be compared
- [ ] All tests pass

**Metrics to Record**:
- Single simulation time: ___ ms
- 200 simulations (serial): ___ seconds
- 200 simulations (parallel): ___ seconds
- Speedup: ___x

**Next Phase**: Sensitivity Analysis

---

## PHASE 4: SENSITIVITY ANALYSIS

### Overview
Analyze how pit stop timing affects expected finishing position.

---

### 4.1 DEVELOP - Single Pit Analysis

**File**: `src/sensitivity.py`

**Tasks**:
1. Create `StrategySensitivityAnalyzer` class
2. Implement `analyze_pit_timing()` method
   - Vary single pit lap ±range
   - Evaluate each variant
   - Return DataFrame with results

**Expected Output**:
- DataFrame with columns: pit_lap, mean_position, std_position
- Identifies optimal pit lap
- Shows sensitivity (steepness of curve)

**Validation**:
```python
# Test sensitivity analysis
analyzer = StrategySensitivityAnalyzer(evaluator)
df = analyzer.analyze_pit_timing(strategy, pit_index=0, lap_range=(40, 70))

assert 'pit_lap' in df.columns
assert 'mean_position' in df.columns
assert len(df) > 0
```

---

### 4.2 DEVELOP - Optimization

**File**: `src/sensitivity.py` (continued)

**Tasks**:
1. Implement `find_optimal_pit_lap()` method
   - Use scipy.optimize.minimize_scalar
   - Find lap that minimizes expected position
   - Return optimal lap and improvement

**Expected Output**:
- Finds optimal lap efficiently
- Compares to original strategy

**Validation**:
```python
# Test optimization
result = analyzer.find_optimal_pit_lap(strategy, pit_index=0)

assert 'optimal_lap' in result
assert 'improvement' in result
```

---

### 4.3 ANALYZE - Sensitivity Curves

**File**: `tests/test_sensitivity.py`

**Tasks**:
1. Test pit timing analysis
2. Test optimization
3. Plot sensitivity curve (optional)
4. Verify curve shape makes sense

**Expected Output**:
- Sensitivity curves show U-shape (optimal in middle)
- Optimal lap is realistic
- All tests pass

**Validation**:
```bash
pytest tests/test_sensitivity.py -v
```

---

### 4.4 CONTROL - Sign-off Checklist

**Verify**:
- [ ] Sensitivity analysis completes in < 2 minutes
- [ ] Curves show realistic shape
- [ ] Optimal laps are reasonable
- [ ] All tests pass

**Metrics to Record**:
- Sensitivity analysis time: ___ seconds
- Optimal pit window: laps ___ to ___
- Position improvement from optimization: ___ positions

**Next Phase**: Validation & Config

---

## PHASE 5: VALIDATION & CONFIG

### Overview
Add validation layer to ensure simulations are realistic.

---

### 5.1 DEVELOP - Validation Checks

**File**: `src/validation.py`

**Tasks**:
1. Create `SimulationValidator` class
2. Implement `validate_lap_times()` method
3. Implement `validate_positions()` method
4. Implement `validate_tire_degradation()` method
5. Implement `validate_race_result()` method

**Expected Output**:
- All validation methods return dict with 'passes' key
- Realistic bounds defined in config

**Validation**:
```python
# Test validator
validator = SimulationValidator()
result = sim.simulate_race()
checks = validator.validate_race_result(result)

assert checks['passes']
```

---

### 5.2 ANALYZE - Realism Testing

**File**: `tests/test_validation.py`

**Tasks**:
1. Test all validation methods
2. Test on good simulation
3. Test on bad simulation (should fail)
4. Document realistic bounds

**Expected Output**:
- Good simulations pass
- Bad simulations fail
- All tests pass

**Validation**:
```bash
pytest tests/test_validation.py -v
```

---

### 5.3 CONTROL - Sign-off Checklist

**Verify**:
- [ ] Validator catches unrealistic simulations
- [ ] Realistic simulations pass all checks
- [ ] Config centralized
- [ ] All tests pass

**Metrics to Record**:
- Validation check time: ___ ms
- Pass rate on 100 random simulations: ___%

**Next Phase**: Dashboard

---

## PHASE 6: DASHBOARD

### Overview
Build Streamlit dashboard for visualization and interaction.

---

### 6.1 DEVELOP - Basic Dashboard

**File**: `app.py`

**Tasks**:
1. Create Streamlit app structure
2. Add strategy comparison tab
3. Add position distribution plot
4. Add sensitivity analysis tab

**Expected Output**:
- Dashboard runs without errors
- Shows strategy comparison table
- Displays histograms

**Validation**:
```bash
streamlit run app.py
```

---

### 6.2 DEVELOP - Advanced Features

**File**: `app.py` (continued)

**Tasks**:
1. Add position-over-time plot
2. Add caution model tab
3. Add live prediction
4. Style with CSS

**Expected Output**:
- All visualizations work
- Interactive elements functional
- Professional appearance

**Validation**:
- Manual testing of all features
- Check for errors

---

### 6.3 CONTROL - Final Sign-off

**Verify**:
- [ ] Dashboard loads in < 5 seconds
- [ ] All plots render correctly
- [ ] Strategies can be compared
- [ ] Sensitivity analysis works
- [ ] Caution predictions display

**Final Metrics**:
- Total code lines: ___
- Test coverage: ___%
- Documentation complete: Yes/No

---

## 🎯 AGENT USAGE GUIDE

### When to Use Different Agents

**Use Me (Main Conversation)**:
- Planning and architecture
- Code review and guidance
- Problem-solving and debugging
- Project coordination

**Use General-Purpose Agent** (via Agent tool) for:
- Researching specific algorithms
- Looking up library documentation
- Finding code examples
- Exploring codebase for patterns

**Use Explore Agent** for:
- Finding specific files or patterns
- Searching codebase
- Understanding existing structure

### Execution Flow

1. **Start Phase**: Read the phase requirements
2. **Develop**: Write code (use me for guidance)
3. **Analyze**: Run tests (use me for debugging)
4. **Control**: Verify and sign-off
5. **Repeat**: Move to next phase

---

## 📝 TRACKING YOUR PROGRESS

Mark each checkbox as you complete:

**Phase 1: Simulator**
- [ ] 1.1 Data structures
- [ ] 1.2 Lap time calculation
- [ ] 1.3 Traffic effects
- [ ] 1.4 Simulation loop
- [ ] 1.5 Physics validation
- [ ] 1.6 Sign-off

**Phase 2: Caution Model**
- [ ] 2.1 Feature engineering
- [ ] 2.2 XGBoost model
- [ ] 2.3 Model evaluation
- [ ] 2.4 Sign-off

**Phase 3: Monte Carlo**
- [ ] 3.1 Single simulation
- [ ] 3.2 Parallel evaluator
- [ ] 3.3 Performance testing
- [ ] 3.4 Sign-off

**Phase 4: Sensitivity**
- [ ] 4.1 Pit timing analysis
- [ ] 4.2 Optimization
- [ ] 4.3 Curve analysis
- [ ] 4.4 Sign-off

**Phase 5: Validation**
- [ ] 5.1 Validation checks
- [ ] 5.2 Realism testing
- [ ] 5.3 Sign-off

**Phase 6: Dashboard**
- [ ] 6.1 Basic dashboard
- [ ] 6.2 Advanced features
- [ ] 6.3 Final sign-off

---

Ready to start? Begin with **Phase 1.1** - Core Data Structures!
