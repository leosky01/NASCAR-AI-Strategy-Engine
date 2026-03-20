"""
NASCAR Race Simulator - Physics-based probabilistic model

This simulator models NASCAR races using lap time decomposition:
Lap_Time = Base + Tire_Effect + Fuel_Effect + Traffic_Penalty + Noise

Positions are determined by sorting cumulative race times, ensuring
physical consistency (not random position swapping).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
from config import DEFAULT_SIM_CONFIG


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

    def get_tire_penalty(self) -> float:
        """
        Calculate lap time penalty from tire degradation.

        Uses exponential curve: degradation accelerates as tires age.
        New tires (age=0) have no penalty.
        Old tires (age=50+) have significant penalty.

        The penalty is capped at a realistic maximum (5 seconds) to prevent
        unrealistic lap times on extremely old tires.

        Returns:
            Lap time penalty in seconds
        """
        # Exponential degradation factor
        degradation_factor = 1 - np.exp(-self.tire_age / 20.0)

        # Base penalty grows with age
        base_penalty = self.physics.tire_degradation_rate * self.tire_age

        # Total penalty increases with age (acceleration)
        penalty = base_penalty * (1 + degradation_factor)

        # Cap at realistic maximum (tires can't make you 10+ seconds slower)
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


@dataclass
class PitStop:
    """
    Pit stop configuration.

    Represents a single pit stop event.
    """
    lap: int
    duration: float = 19.5  # seconds (includes enter/exit/stop)
    fuel_added: float = 100.0  # percentage
    tires_changed: bool = True


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
                 random_seed: Optional[int] = None):
        """
        Initialize simulator.

        Args:
            num_cars: Number of cars in race
            num_laps: Total race laps
            track_length: Track length in miles
            random_seed: For reproducibility
        """
        self.num_cars = num_cars
        self.num_laps = num_laps
        self.track_length = track_length
        self.rng = np.random.RandomState(random_seed)

        # Load config
        self.config = DEFAULT_SIM_CONFIG

        # Simulation state
        self.cars: List[CarState] = []
        self.caution_active = False
        self.caution_remaining = 0
        self.lap_history: List[Dict] = []

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

    def calculate_lap_time(self, car: CarState, traffic_penalty: float = 0.0) -> float:
        """
        Calculate lap time from physical components.

        Lap_Time = Base + Tire_Penalty + Fuel_Penalty + Traffic + Noise

        Args:
            car: Car state
            traffic_penalty: Time penalty from following slower cars

        Returns:
            Lap time in seconds
        """
        # Sum components
        lap_time = (
            car.physics.base_lap_time +
            car.get_tire_penalty() +
            car.get_fuel_penalty() +
            traffic_penalty +
            car.get_noise()
        )

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

    def simulate_lap(self, lap: int, strategy_pits: Dict[int, PitStop]) -> List[CarState]:
        """
        Simulate a single lap for all cars.

        Iterative approach: calculate tentative times, apply traffic
        penalties, recalculate. Repeats for convergence.

        Args:
            lap: Current lap number
            strategy_pits: Dict mapping lap to PitStop

        Returns:
            Updated car states
        """
        # First pass: handle pit stops and calculate tentative lap times (no traffic)
        tentative_lap_times = {}
        for car in self.cars:
            # Check for pit stop
            if lap in strategy_pits:
                pit = strategy_pits[lap]
                car.cumulative_time += pit.duration
                if pit.tires_changed:
                    car.tire_age = 0
                car.fuel_level = min(100.0, car.fuel_level + pit.fuel_added)
                # Record pit duration as the lap time (for accurate statistics)
                tentative_lap_times[car.car_id] = pit.duration
            else:
                # Calculate tentative lap time (without traffic)
                tentative_time = self.calculate_lap_time(car, traffic_penalty=0.0)
                tentative_lap_times[car.car_id] = tentative_time

            # Consume fuel and age tires (if not pitting or pit didn't change tires)
            if lap not in strategy_pits or not strategy_pits[lap].tires_changed:
                car.fuel_level -= self.config.fuel_consumption_per_lap
                car.tire_age += 1

        # Second pass: apply traffic effects and finalize lap times
        # First iteration: calculate with current positions
        sorted_times = sorted(
            [(car.car_id, car.cumulative_time) for car in self.cars],
            key=lambda x: x[1]
        )

        final_lap_times = {}
        for car in self.cars:
            if lap in strategy_pits:
                # Pitting car - lap time is already set to pit duration
                car.current_lap_time = tentative_lap_times[car.car_id]
                final_lap_times[car.car_id] = car.current_lap_time
                # No additional cumulative time added (pit duration already added)
            else:
                # Regular lap - apply traffic penalty
                traffic_penalty = self.calculate_traffic_penalty(car, sorted_times)
                final_time = self.calculate_lap_time(car, traffic_penalty=traffic_penalty)
                final_lap_times[car.car_id] = final_time
                car.current_lap_time = final_time
                car.cumulative_time += final_time

        # Update positions based on cumulative time
        sorted_cars = sorted(self.cars, key=lambda c: c.cumulative_time)
        for position, car in enumerate(sorted_cars):
            car.position = position + 1

        return self.cars

    def simulate_race(self, strategy: Optional[Dict[int, List[PitStop]]] = None) -> Dict:
        """
        Simulate complete race.

        Args:
            strategy: Dict mapping car_id to list of pit stops

        Returns:
            Dict with final positions, times, and lap history
        """
        if strategy is None:
            strategy = {}

        # Initialize
        self.initialize_cars()

        # Flatten strategy for easy lookup by lap
        strategy_pits = {}
        for car_id, pits in strategy.items():
            for pit in pits:
                strategy_pits[pit.lap] = pit

        # Clear history
        self.lap_history = []

        # Simulate each lap
        for lap in range(1, self.num_laps + 1):
            self.cars = self.simulate_lap(lap, strategy_pits)

            # Record history
            self.lap_history.append({
                'lap': lap,
                'positions': [car.position for car in self.cars],
                'lap_times': [car.current_lap_time for car in self.cars],
                'tire_ages': [car.tire_age for car in self.cars],
                'fuel_levels': [car.fuel_level for car in self.cars],
            })

        # Find winner
        winner = min(self.cars, key=lambda c: c.cumulative_time).car_id

        return {
            'final_positions': {car.car_id: car.position for car in self.cars},
            'final_times': {car.car_id: car.cumulative_time for car in self.cars},
            'lap_history': self.lap_history,
            'winner': winner
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
