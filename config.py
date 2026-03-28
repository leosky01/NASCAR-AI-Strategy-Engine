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
    fuel_consumption_per_lap: float = 0.80  # percentage (~125 laps on full tank, realistic for 1.5-mile tracks)

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


@dataclass
class PointsConfig:
    """NASCAR stage points configuration"""
    stage1_lap: int = 60
    stage2_lap: int = 120
    stage_points: tuple = (10, 9, 8, 7, 6, 5, 4, 3, 2, 1)  # Top 10 positions
    winner_points: int = 40
    second_place_points: int = 35
    third_place_points: int = 34


@dataclass
class TireModelConfig:
    """GAM tire model configuration"""
    use_gam_model: bool = False
    default_track: str = 'Charlotte'
    available_tracks: tuple = ('Phoenix', 'Charlotte', 'Darlington', 'Bristol', 'Talladega')
    use_synthetic_data: bool = True
    synthetic_samples_per_track: int = 1000


@dataclass
class TrackProfile:
    """Track-specific race parameters."""
    name: str
    length_miles: float
    num_laps: int
    stage1_end: int
    stage2_end: int
    base_lap_time: float  # seconds
    tire_degradation_rate: float  # seconds per lap
    caution_base_prob: float
    traffic_penalty_factor: float
    description: str


# Real NASCAR track profiles with realistic parameters
TRACK_PROFILES = {
    'Phoenix': TrackProfile(
        name='Phoenix Raceway',
        length_miles=1.0,
        num_laps=312,
        stage1_end=75,
        stage2_end=190,
        base_lap_time=27.0,
        tire_degradation_rate=0.10,
        caution_base_prob=0.015,
        traffic_penalty_factor=0.7,
        description='1-mile oval, moderate banking (11°), high tire wear'
    ),
    'Charlotte': TrackProfile(
        name='Charlotte Motor Speedway',
        length_miles=1.5,
        num_laps=267,
        stage1_end=65,
        stage2_end=130,
        base_lap_time=30.5,
        tire_degradation_rate=0.08,
        caution_base_prob=0.012,
        traffic_penalty_factor=0.8,
        description='1.5-mile quad-oval, 24° banking, moderate tire wear'
    ),
    'Darlington': TrackProfile(
        name='Darlington Raceway',
        length_miles=1.366,
        num_laps=293,
        stage1_end=70,
        stage2_end=185,
        base_lap_time=29.0,
        tire_degradation_rate=0.13,
        caution_base_prob=0.018,
        traffic_penalty_factor=0.9,
        description='1.366-mile egg-shaped oval, 25° banking, "Too Tough to Tame" — very high tire wear'
    ),
    'Bristol': TrackProfile(
        name='Bristol Motor Speedway',
        length_miles=0.533,
        num_laps=500,
        stage1_end=125,
        stage2_end=250,
        base_lap_time=16.0,
        tire_degradation_rate=0.11,
        caution_base_prob=0.020,
        traffic_penalty_factor=1.0,
        description='0.533-mile short track, 26° banking, high caution rate, close racing'
    ),
    'Talladega': TrackProfile(
        name='Talladega Superspeedway',
        length_miles=2.66,
        num_laps=188,
        stage1_end=60,
        stage2_end=120,
        base_lap_time=50.0,
        tire_degradation_rate=0.04,
        caution_base_prob=0.010,
        traffic_penalty_factor=1.2,
        description='2.66-mile superspeedway, 33° banking, pack racing, low tire wear'
    )
}


# Default configurations
DEFAULT_SIM_CONFIG = SimulatorConfig()
DEFAULT_MODEL_CONFIG = ModelConfig()
DEFAULT_MC_CONFIG = MonteCarloConfig()
DEFAULT_SENSITIVITY_CONFIG = SensitivityConfig()
DEFAULT_VALIDATION_CONFIG = ValidationConfig()
DEFAULT_POINTS_CONFIG = PointsConfig()
DEFAULT_TIRE_MODEL_CONFIG = TireModelConfig()
