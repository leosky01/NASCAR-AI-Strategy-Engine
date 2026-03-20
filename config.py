"""
Central configuration for NASCAR AI Strategy Engine.

All magic numbers and parameters should be defined here.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class SimulatorConfig:
    """Physics parameters for race simulation"""
    # Race parameters
    num_cars: int = 40
    num_laps: int = 200
    track_length: float = 2.5  # miles

    # Lap time bounds (seconds)
    min_lap_time: float = 45.0
    max_lap_time: float = 55.0

    # Lap time physics (seconds)
    base_lap_time: float = 48.0
    lap_time_std: float = 0.15  # Gaussian noise

    # Tire degradation
    tire_degradation_rate: float = 0.08  # seconds per lap (new tires)
    tire_degradation_acceleration: float = 0.05  # exponential factor
    expected_tire_life: int = 50  # laps

    # Fuel effects
    fuel_weight_penalty: float = 0.03  # seconds per percentage point
    fuel_consumption_per_lap: float = 0.25  # percentage

    # Traffic effects
    traffic_penalty_factor: float = 0.8  # max seconds
    dirty_air_threshold: float = 0.5  # seconds behind car ahead

    # Cautions
    caution_base_prob: float = 0.012
    caution_duration_laps: int = 4
    caution_slowdown_factor: float = 1.25  # 25% slower under yellow

    # Pit stops
    pit_stop_duration: float = 19.5  # seconds


@dataclass
class ModelConfig:
    """Machine learning model configuration"""
    # XGBoost hyperparameters
    n_estimators: int = 100
    max_depth: int = 4
    learning_rate: float = 0.05
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    scale_pos_weight: float = 10  # for class imbalance

    # Training
    train_test_split: float = 0.2
    random_state: int = 42
    prediction_horizon: int = 5  # laps to look ahead


@dataclass
class MonteCarloConfig:
    """Monte Carlo evaluation configuration"""
    default_simulations: int = 200
    min_simulations: int = 50
    max_simulations: int = 1000
    n_jobs: int = -1  # -1 = use all CPUs


@dataclass
class SensitivityConfig:
    """Sensitivity analysis and optimization configuration"""
    # Grid search parameters
    default_lap_range: tuple = (35, 65)  # default search range
    default_lap_step: int = 2  # laps to step in grid search

    # Optimization parameters
    optimization_tolerance: float = 2.0  # xatol for scipy minimize
    min_search_lap: int = 30  # minimum lap to consider for pit
    max_search_lap: int = 180  # maximum lap to consider for pit

    # Simulation quality vs speed tradeoff
    quick_sims_per_point: int = 10  # fast but noisy
    standard_sims_per_point: int = 30  # balanced
    thorough_sims_per_point: int = 50  # slow but accurate


# Validation thresholds
@dataclass
class ValidationConfig:
    """Reasonable bounds for NASCAR racing"""
    min_lap_time: float = 45.0  # seconds
    max_lap_time: float = 55.0  # seconds
    min_cautions_per_race: int = 3
    max_cautions_per_race: int = 12
    min_tire_life: int = 40  # laps
    max_tire_life: int = 70  # laps


# Default configurations
DEFAULT_SIM_CONFIG = SimulatorConfig()
DEFAULT_MODEL_CONFIG = ModelConfig()
DEFAULT_MC_CONFIG = MonteCarloConfig()
DEFAULT_SENSITIVITY_CONFIG = SensitivityConfig()
DEFAULT_VALIDATION_CONFIG = ValidationConfig()
