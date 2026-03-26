"""
NASCAR Race Simulator - Physics-based probabilistic model

This simulator models NASCAR races using lap time decomposition:
Lap_Time = Base + Tire_Effect + Fuel_Effect + Traffic_Penalty + Noise

Positions are determined by sorting cumulative race times, ensuring
physical consistency (not random position swapping).
"""
from dataclasses import dataclass, field
from copy import deepcopy
from typing import List, Dict, Optional, Tuple
import numpy as np
from config import DEFAULT_SIM_CONFIG
from src.strategy import PitStop


@dataclass
class CarPhysics:
    """
    Physics parameters for a car (driver/team characteristics).

    These parameters represent the intrinsic capabilities of a driver
    and team combination that persist throughout a race.
    """
    base_lap_time: float = 48.0  # seconds, baseline speed
    tire_degradation_rate: float = 0.08  # seconds per lap (new tires)
    fuel_weight_penalty: float = 0.03  # seconds per % fuel
    overtaking_ability: float = 1.0  # multiplier for traffic effect (higher = better)
    consistency: float = 1.0  # noise multiplier (lower = more consistent)
    use_gam_model: bool = False  # Use GAM tire model if available
    track_name: str = 'Charlotte'  # For GAM tire model lookup


@dataclass
class CarState:
    """
    Dynamic state of a car during race.

    Changes each lap based on simulation.
    Position is determined by cumulative time, not updated directly.
    """
    car_id: int
    physics: CarPhysics
    cumulative_time: float = 0.0
    tire_age: int = 0
    fuel_level: float = 100.0  # percentage
    current_lap_time: float = 0.0
    position: int = 1

    def get_tire_penalty(self, tire_model_manager=None, traffic_density=0.0) -> float:
        """
        Calculate lap time penalty from tire degradation.

        Uses GAM model if available and enabled, otherwise falls back to
        exponential curve: degradation accelerates as tires age.

        Args:
            tire_model_manager: Optional TireModelManager for GAM predictions
            traffic_density: Current traffic density (0-1) for GAM model

        Returns:
            Lap time penalty in seconds
        """
        # Use GAM if available and enabled
        if (tire_model_manager and
            self.physics.use_gam_model and
            hasattr(tire_model_manager, 'predict_tire_penalty')):
            from src.tire_model import TireModelManager
            if isinstance(tire_model_manager, TireModelManager):
                result = tire_model_manager.predict_tire_penalty(
                    track_name=self.physics.track_name,
                    tire_age=self.tire_age,
                    traffic_density=traffic_density,
                    overtaking_ability=self.physics.overtaking_ability
                )
                return min(result.predicted_penalty, 5.0)

        # Fallback to exponential model (backward compatible)
        degradation_factor = 1 - np.exp(-self.tire_age / 20.0)
        base_penalty = self.physics.tire_degradation_rate * self.tire_age
        penalty = base_penalty * (1 + degradation_factor)
        return min(penalty, 5.0)

    def get_fuel_penalty(self) -> float:
        """
        Calculate lap time penalty from fuel weight.

        Heavier car (more fuel) = slower lap times.
        Linear relationship with fuel level.

        Returns:
            Lap time penalty in seconds
        """
        return self.physics.fuel_weight_penalty * self.fuel_level

    def get_noise(self) -> float:
        """
        Calculate lap time variability (driver consistency).

        More consistent drivers have smaller variance.
        Random Gaussian noise.

        Returns:
            Random time adjustment in seconds
        """
        return np.random.normal(0, 0.15 * self.physics.consistency)


class RaceSimulator:
    """
    Physics-based NASCAR race simulator.

    Uses lap time decomposition model where position is determined
    by sorting cumulative race times.
    """

    def __init__(self,
                 num_cars: int = 40,
                 num_laps: int = 200,
                 track_length: float = 2.5,
                 random_seed: Optional[int] = None,
                 caution_model: Optional['CautionPredictor'] = None):
        """
        Initialize simulator.

        Args:
            num_cars: Number of cars in race
            num_laps: Total race laps
            track_length: Track length in miles
            random_seed: For reproducibility
            caution_model: Optional ML model for caution prediction
        """
        self.num_cars = num_cars
        self.num_laps = num_laps
        self.track_length = track_length
        self.rng = np.random.RandomState(random_seed)
        self.caution_model = caution_model

        # Load config (deep copy to avoid mutating global default)
        self.config = deepcopy(DEFAULT_SIM_CONFIG)

        # Simulation state
        self.cars: List[CarState] = []
        self.caution_active = False
        self.caution_remaining = 0
        self.green_flag_run_length = 0  # Laps since last caution
        self.lap_history: List[Dict] = []

        # Stage tracking (for NASCAR stage racing)
        # Default stages: laps 60 and 120 for a 200 lap race
        self.stage_laps = [max(1, num_laps // 3), max(1, 2 * num_laps // 3)]
        self.stage_positions: Dict[int, Dict[int, int]] = {}  # {stage_num: {car_id: position}}

        # Tire model manager (optional, for GAM-based tire degradation)
        self.tire_model_manager = None

    def set_tire_model_manager(self, tire_model_manager):
        """
        Set the tire model manager for GAM-based tire degradation.

        Args:
            tire_model_manager: TireModelManager instance
        """
        self.tire_model_manager = tire_model_manager

    def _calculate_traffic_density(self, car: CarState, sorted_times: List[Tuple[int, float]]) -> float:
        """
        Calculate traffic density (0-1) for a car.

        Based on how many cars are close ahead.

        Args:
            car: Car state
            sorted_times: List of (car_id, cumulative_time) sorted by time

        Returns:
            Traffic density from 0 (none) to 1 (heavy)
        """
        # Find our position
        our_idx = next((i for i, (car_id, _) in enumerate(sorted_times) if car_id == car.car_id), None)

        if our_idx is None or our_idx == 0:
            return 0.0  # Leader has no traffic

        # Count cars within 1 second ahead
        cars_within_1s = 0
        for i in range(max(0, our_idx - 10), our_idx):  # Check up to 10 cars ahead
            _, ahead_time = sorted_times[i]
            _, our_time = sorted_times[our_idx]
            gap = our_time - ahead_time
            if gap <= 1.0:
                cars_within_1s += 1

        # Normalize to 0-1 (10 cars within 1s = max density)
        return min(cars_within_1s / 10.0, 1.0)

    def initialize_cars(self, car_physics: Optional[List[CarPhysics]] = None):
        """
        Initialize car states with physics parameters.

        If no physics provided, generates varied parameters to represent
        different driver/team skill levels.

        Args:
            car_physics: Optional list of physics for each car
        """
        if car_physics is None:
            # Generate varied car physics (driver/team skill)
            car_physics = []
            for i in range(self.num_cars):
                # Varied base times (48.0 to 49.5)
                base_time = self.config.base_lap_time + self.rng.exponential(0.5)

                # Some drivers better on tires (lower degradation)
                tire_rate = self.rng.gamma(2, 0.04)

                physics = CarPhysics(
                    base_lap_time=base_time,
                    tire_degradation_rate=tire_rate,
                    fuel_weight_penalty=self.config.fuel_weight_penalty,
                    overtaking_ability=self.rng.beta(3, 2),  # 0-1, skewed high
                    consistency=self.rng.beta(4, 2)  # 0-1, skewed high
                )
                car_physics.append(physics)

        self.cars = [
            CarState(car_id=i, physics=car_physics[i])
            for i in range(self.num_cars)
        ]

    def calculate_lap_time(self, car: CarState, traffic_penalty: float = 0.0, traffic_density: float = 0.0, skip_noise: bool = False) -> float:
        """
        Calculate lap time from physical components.

        Lap_Time = Base + Tire_Penalty + Fuel_Penalty + Traffic + Noise

        Args:
            car: Car state
            traffic_penalty: Time penalty from following slower cars
            traffic_density: Traffic density (0-1) for GAM tire model
            skip_noise: If True, skip random noise (useful for deterministic first lap)

        Returns:
            Lap time in seconds
        """
        # Sum components
        lap_time = (
            car.physics.base_lap_time +
            car.get_tire_penalty(self.tire_model_manager, traffic_density) +
            car.get_fuel_penalty() +
            traffic_penalty
        )

        # Add noise (unless skipped) - use seeded RNG for reproducibility
        if not skip_noise:
            lap_time += self.rng.normal(0, 0.15 * car.physics.consistency)

        # Cautions slow everyone down
        if self.caution_active:
            lap_time *= self.config.caution_slowdown_factor

        return max(self.config.min_lap_time, lap_time)

    def calculate_traffic_penalty(self, car: CarState, sorted_times: List[Tuple[int, float]]) -> float:
        """
        Calculate time penalty from traffic (dirty air effect).

        Cars close behind slower cars experience reduced aerodynamics,
        increasing lap time. Penalty based on gap and overtaking ability.

        Args:
            car: Car state
            sorted_times: List of (car_id, cumulative_time) sorted by time

        Returns:
            Time penalty in seconds
        """
        # Find our position in sorted times
        our_idx = next((i for i, (car_id, _) in enumerate(sorted_times) if car_id == car.car_id), None)

        if our_idx is None or our_idx == 0:
            return 0.0  # Leader has clean air

        # Get gap to car ahead (positive means we're behind)
        _, ahead_time = sorted_times[our_idx - 1]
        _, our_time = sorted_times[our_idx]
        gap = our_time - ahead_time  # Positive = behind, 0 = even

        if gap > 1.0:
            return 0.0  # Too far behind to be affected

        # Penalty increases as gap decreases, modified by overtaking ability
        gap_factor = max(0, (1.0 - gap) / 1.0)  # 0 to 1
        penalty = self.config.traffic_penalty_factor * gap_factor / car.physics.overtaking_ability

        # Cap at realistic maximum (dirty air can't make you 2+ seconds slower)
        return min(penalty, 1.0)

    def simulate_lap(self, lap: int, strategy_pits: Dict[int, Dict[int, PitStop]]) -> List[CarState]:
        """
        Simulate a single lap for all cars.

        Iterative approach: calculate tentative times, apply traffic
        penalties, recalculate. Repeats for convergence.

        Args:
            lap: Current lap number
            strategy_pits: Dict mapping car_id to lap to PitStop

        Returns:
            Updated car states
        """
        # First pass: handle pit stops and calculate tentative lap times (no traffic)
        tentative_lap_times = {}
        for car in self.cars:
            # Check for pit stop for this specific car
            car_pits = strategy_pits.get(car.car_id, {})
            if lap in car_pits:
                pit = car_pits[lap]
                car.cumulative_time += pit.duration
                if pit.tires_changed:
                    car.tire_age = 0
                car.fuel_level = min(100.0, car.fuel_level + pit.fuel_added)
                # Record pit duration as the lap time (for accurate statistics)
                tentative_lap_times[car.car_id] = pit.duration
            else:
                # Calculate tentative lap time (without traffic)
                # Skip noise on first lap for deterministic starting positions
                tentative_time = self.calculate_lap_time(car, traffic_penalty=0.0, skip_noise=(lap == 1))
                tentative_lap_times[car.car_id] = tentative_time

            # Consume fuel and age tires (if not pitting or pit didn't change tires)
            if lap not in car_pits or not car_pits[lap].tires_changed:
                car.fuel_level -= self.config.fuel_consumption_per_lap
                car.tire_age += 1

        # Second pass: apply traffic effects and finalize lap times
        # Sort by tentative lap times to calculate realistic traffic penalties
        sorted_times = sorted(
            [(car.car_id, car.cumulative_time + tentative_lap_times[car.car_id]) for car in self.cars],
            key=lambda x: x[1]
        )

        final_lap_times = {}
        for car in self.cars:
            car_pits = strategy_pits.get(car.car_id, {})
            if lap in car_pits:
                # Pitting car - lap time is already set to pit duration
                car.current_lap_time = tentative_lap_times[car.car_id]
                final_lap_times[car.car_id] = car.current_lap_time
                # No additional cumulative time added (pit duration already added)
            else:
                # Calculate traffic density for GAM model
                traffic_density = self._calculate_traffic_density(car, sorted_times)

                # Regular lap - apply traffic penalty to tentative time
                # (Don't recalculate lap time, just add traffic penalty to avoid regenerating noise)
                traffic_penalty = self.calculate_traffic_penalty(car, sorted_times)
                final_time = tentative_lap_times[car.car_id] + traffic_penalty
                final_lap_times[car.car_id] = final_time
                car.current_lap_time = final_time
                car.cumulative_time += final_time

        # Update positions based on cumulative time
        sorted_cars = sorted(self.cars, key=lambda c: c.cumulative_time)
        for position, car in enumerate(sorted_cars):
            car.position = position + 1

        return self.cars

    def _generate_default_strategy(self, car_id: int) -> List[PitStop]:
        """
        Generate a reasonable default pit strategy for a car.

        Default strategy: pit every ~50 laps with fuel and tires.

        Args:
            car_id: Car identifier

        Returns:
            List of PitStop objects
        """
        pit_laps = []
        lap = 50
        while lap < self.num_laps:
            # Add some variation based on car_id (simulates different team strategies)
            variation = (car_id % 5) - 2  # -2 to +2
            pit_lap = max(40, min(lap + variation, self.num_laps - 10))
            pit_laps.append(pit_lap)
            lap += 50

        return [PitStop(lap=lap) for lap in pit_laps]

    def _calculate_caution_probability(self, lap: int) -> float:
        """
        Calculate probability of a caution occurring on this lap.

        Uses probabilistic model with optional ML enhancement.

        Args:
            lap: Current lap number

        Returns:
            Caution probability (0-1)
        """
        # If ML model is provided, use it
        if self.caution_model is not None and self.caution_model.is_trained:
            try:
                # Calculate features for current race state
                avg_tire_age = np.mean([car.tire_age for car in self.cars])
                features = {
                    'race_progress': lap / self.num_laps,
                    'laps_remaining': max(0, self.num_laps - lap),
                    'current_lap_norm': lap / self.num_laps,
                    'cautions_so_far': sum(1 for h in self.lap_history if h.get('caution_active', False)),
                    'laps_since_last_caution': self.green_flag_run_length,
                    'caution_density': 0.0,  # Would need full history
                    'green_flag_run_length': self.green_flag_run_length,
                    'long_green_flag': int(self.green_flag_run_length > 40),
                    'lap_time_variance': 0.0,  # Simplified
                    'field_spread': 0.0,  # Simplified
                    'avg_tire_age': avg_tire_age,
                    'max_tire_age': max(car.tire_age for car in self.cars),
                    'tired_cars_pct': np.mean([car.tire_age > 40 for car in self.cars]),
                    'avg_position_change': 0.0,  # Simplified
                    'max_position_change': 0.0,  # Simplified
                    'position_volatility': 0.0,  # Simplified
                    'risk_accumulation': (avg_tire_age / 50.0) * (self.green_flag_run_length / 50.0) * (lap / self.num_laps),
                    'caution_likelihood_score': (avg_tire_age / 50.0) * 0.3 + (self.green_flag_run_length / 100.0) * 0.3 + (lap / self.num_laps) * 0.2
                }
                return self.caution_model.predict_caution_probability(features)
            except Exception:
                # Fall back to simple model if prediction fails
                pass

        # Simple probabilistic model (default)
        base_prob = self.config.caution_base_prob

        # Increase probability with tire wear across the field
        avg_tire_age = np.mean([car.tire_age for car in self.cars])
        tire_factor = 1.0 + (avg_tire_age / 50.0)  # Up to 2x probability

        # Increase probability with long green flag runs
        green_flag_factor = 1.0 + (self.green_flag_run_length / 100.0)  # Up to 2x

        # Increase probability late in race
        race_progress = lap / self.num_laps
        late_race_factor = 1.0 + (race_progress * 0.5)  # Up to 1.5x

        # Combine factors
        prob = base_prob * tire_factor * green_flag_factor * late_race_factor

        # Cap at reasonable maximum
        return min(prob, 0.10)  # Max 10% per lap

    def simulate_race(self, strategy: Optional[Dict[int, List[PitStop]]] = None, skip_init: bool = False) -> Dict:
        """
        Simulate complete race.

        Args:
            strategy: Dict mapping car_id to list of pit stops
            skip_init: If True, skip car initialization (useful for pre-configured cars)

        Returns:
            Dict with final positions, times, and lap history
        """
        if strategy is None:
            strategy = {}

        # Initialize (unless skipped)
        if not skip_init:
            self.initialize_cars()

        # Reset caution state
        self.caution_active = False
        self.caution_remaining = 0
        self.green_flag_run_length = 0

        # Build complete strategy with defaults for cars without specified strategies
        # Structure: strategy_pits[car_id][lap] = PitStop
        strategy_pits: Dict[int, Dict[int, PitStop]] = {}

        for car_id in range(self.num_cars):
            if car_id in strategy and strategy[car_id]:
                # Use provided strategy for this car
                car_pits = {}
                for pit in strategy[car_id]:
                    car_pits[pit.lap] = pit
                strategy_pits[car_id] = car_pits
            else:
                # Generate default strategy for this car
                default_pits = self._generate_default_strategy(car_id)
                car_pits = {pit.lap: pit for pit in default_pits}
                strategy_pits[car_id] = car_pits

        # Clear history
        self.lap_history = []

        # Simulate each lap
        for lap in range(1, self.num_laps + 1):
            # Check for caution triggering (only if not already under caution)
            if not self.caution_active:
                caution_prob = self._calculate_caution_probability(lap)
                if self.rng.random() < caution_prob:
                    # Caution triggered!
                    self.caution_active = True
                    self.caution_remaining = self.config.caution_duration_laps
                    self.green_flag_run_length = 0

            self.cars = self.simulate_lap(lap, strategy_pits)

            # Update caution state
            if self.caution_active:
                self.caution_remaining -= 1
                if self.caution_remaining <= 0:
                    self.caution_active = False
            else:
                self.green_flag_run_length += 1

            # Check for stage end
            if lap in self.stage_laps:
                stage_num = self.stage_laps.index(lap) + 1
                # Record positions at stage end
                self.stage_positions[stage_num] = {
                    car.car_id: car.position for car in self.cars
                }

            # Record history
            self.lap_history.append({
                'lap': lap,
                'positions': [car.position for car in self.cars],
                'lap_times': [car.current_lap_time for car in self.cars],
                'tire_ages': [car.tire_age for car in self.cars],
                'fuel_levels': [car.fuel_level for car in self.cars],
                'caution_active': self.caution_active,
            })

        # Find winner
        winner = min(self.cars, key=lambda c: c.cumulative_time).car_id

        return {
            'final_positions': {car.car_id: car.position for car in self.cars},
            'final_times': {car.car_id: car.cumulative_time for car in self.cars},
            'lap_history': self.lap_history,
            'winner': winner,
            'stage_positions': self.stage_positions
        }

    def validate_simulation(self, result: Dict) -> Dict[str, bool]:
        """
        Run sanity checks on simulation result.

        Args:
            result: Result dict from simulate_race()

        Returns:
            Dict of check names to boolean results
        """
        checks = {}

        # Check all positions are unique
        positions = list(result['final_positions'].values())
        checks['all_positions_unique'] = len(set(positions)) == self.num_cars

        # Check all positions cover 1 to num_cars
        checks['all_positions_valid'] = set(positions) == set(range(1, self.num_cars + 1))

        # Check all times are positive
        times = list(result['final_times'].values())
        checks['all_times_positive'] = all(t > 0 for t in times)

        # Check all times are unique (no ties given randomness)
        checks['all_times_unique'] = len(set(times)) == self.num_cars

        # Check winner is defined
        checks['winner_defined'] = result['winner'] is not None

        # Check lap history has correct length
        checks['lap_history_complete'] = len(result['lap_history']) == self.num_laps

        # Check no zero lap times (except potentially for first lap)
        all_lap_times = []
        for lap_data in result['lap_history']:
            all_lap_times.extend(lap_data['lap_times'])
        checks['no_zero_lap_times'] = all(t > 0 for t in all_lap_times)

        # Check reasonable average lap time
        avg_lap_time = np.mean(all_lap_times)
        checks['reasonable_avg_lap_time'] = 45 < avg_lap_time < 65

        return checks
