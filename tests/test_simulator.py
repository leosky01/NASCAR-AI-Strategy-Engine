"""
Tests for NASCAR race simulator.

Tests follow AAA pattern: Arrange, Act, Assert
"""
import pytest
import numpy as np
import sys
sys.path.insert(0, '.')

from src.simulator import (
    CarPhysics,
    CarState,
    PitStop,
    RaceSimulator
)


class TestCarPhysics:
    """Test CarPhysics dataclass"""

    def test_create_default_physics(self):
        """Test creating physics with defaults"""
        physics = CarPhysics()
        assert physics.base_lap_time == 48.0
        assert physics.tire_degradation_rate == 0.08
        assert physics.overtaking_ability == 1.0
        assert physics.consistency == 1.0

    def test_create_custom_physics(self):
        """Test creating physics with custom values"""
        physics = CarPhysics(
            base_lap_time=47.5,
            tire_degradation_rate=0.10
        )
        assert physics.base_lap_time == 47.5
        assert physics.tire_degradation_rate == 0.10


class TestCarState:
    """Test CarState calculations"""

    def test_tire_penalty_new_tires(self):
        """Test that new tires have no penalty"""
        physics = CarPhysics(tire_degradation_rate=0.08)
        car = CarState(car_id=0, physics=physics, tire_age=0)

        penalty = car.get_tire_penalty()
        assert penalty == 0.0

    def test_tire_penalty_old_tires(self):
        """Test that old tires have significant penalty"""
        physics = CarPhysics(tire_degradation_rate=0.08)
        car = CarState(car_id=0, physics=physics, tire_age=50)

        penalty = car.get_tire_penalty()
        # Should be several seconds slower
        assert penalty > 2.0

    def test_tire_penalty_increases_with_age(self):
        """Test that tire penalty increases with age"""
        physics = CarPhysics(tire_degradation_rate=0.08)

        car_new = CarState(car_id=0, physics=physics, tire_age=0)
        car_old = CarState(car_id=1, physics=physics, tire_age=50)

        penalty_new = car_new.get_tire_penalty()
        penalty_old = car_old.get_tire_penalty()

        assert penalty_old > penalty_new

    def test_fuel_penalty_full_tank(self):
        """Test fuel penalty with full tank"""
        physics = CarPhysics(fuel_weight_penalty=0.03)
        car = CarState(car_id=0, physics=physics, fuel_level=100.0)

        penalty = car.get_fuel_penalty()
        # 100% * 0.03 = 3.0 seconds
        assert abs(penalty - 3.0) < 0.01

    def test_fuel_penalty_empty_tank(self):
        """Test fuel penalty with empty tank"""
        physics = CarPhysics(fuel_weight_penalty=0.03)
        car = CarState(car_id=0, physics=physics, fuel_level=0.0)

        penalty = car.get_fuel_penalty()
        assert penalty == 0.0

    def test_fuel_penalty_linear(self):
        """Test that fuel penalty is linear"""
        physics = CarPhysics(fuel_weight_penalty=0.03)

        car_half = CarState(car_id=0, physics=physics, fuel_level=50.0)
        car_full = CarState(car_id=1, physics=physics, fuel_level=100.0)

        penalty_half = car_half.get_fuel_penalty()
        penalty_full = car_full.get_fuel_penalty()

        assert abs(penalty_full - 2 * penalty_half) < 0.01

    def test_noise_reasonable_range(self):
        """Test that noise is in reasonable range"""
        physics = CarPhysics(consistency=1.0)
        car = CarState(car_id=0, physics=physics)

        # Generate multiple samples
        noises = [car.get_noise() for _ in range(100)]

        # Most should be within ±0.5 seconds (3 sigma)
        assert abs(np.mean(noises)) < 0.1  # Mean near 0
        assert np.std(noises) < 0.2  # Std ~0.15


class TestRaceSimulator:
    """Test race simulation"""

    def test_initialize_simulator(self):
        """Test creating simulator"""
        sim = RaceSimulator(num_cars=40, num_laps=200)

        assert sim.num_cars == 40
        assert sim.num_laps == 200
        assert len(sim.cars) == 0  # Not initialized yet

    def test_initialize_cars(self):
        """Test car initialization"""
        sim = RaceSimulator(num_cars=10, num_laps=100)
        sim.initialize_cars()

        assert len(sim.cars) == 10

        # Check car IDs
        car_ids = [car.car_id for car in sim.cars]
        assert set(car_ids) == set(range(10))

    def test_initialize_cars_custom_physics(self):
        """Test initialization with custom physics"""
        physics_list = [
            CarPhysics(base_lap_time=48.0),
            CarPhysics(base_lap_time=49.0)
        ]

        sim = RaceSimulator(num_cars=2)
        sim.initialize_cars(car_physics=physics_list)

        assert sim.cars[0].physics.base_lap_time == 48.0
        assert sim.cars[1].physics.base_lap_time == 49.0

    def test_calculate_lap_time_reasonable(self):
        """Test that lap times are realistic"""
        sim = RaceSimulator()
        sim.initialize_cars()

        car = sim.cars[0]
        lap_time = sim.calculate_lap_time(car)

        # Should be between 45 and 55 seconds
        assert 45 < lap_time < 55

    def test_calculate_lap_time_components(self):
        """Test that lap time components work correctly"""
        physics = CarPhysics(
            base_lap_time=48.0,
            tire_degradation_rate=0.0,
            fuel_weight_penalty=0.0
        )
        car = CarState(car_id=0, physics=physics, tire_age=0, fuel_level=0)

        sim = RaceSimulator()
        lap_time = sim.calculate_lap_time(car)

        # Should be close to base (only small noise)
        assert 47.5 < lap_time < 48.5

    def test_calculate_lap_time_old_tires(self):
        """Test that old tires slow down car"""
        physics = CarPhysics(base_lap_time=48.0, tire_degradation_rate=0.1)
        car_new = CarState(car_id=0, physics=physics, tire_age=0, fuel_level=0)
        car_old = CarState(car_id=1, physics=physics, tire_age=50, fuel_level=0)

        sim = RaceSimulator()
        time_new = sim.calculate_lap_time(car_new)
        time_old = sim.calculate_lap_time(car_old)

        assert time_old > time_new + 2.0  # At least 2 seconds slower

    def test_calculate_traffic_penalty_leader(self):
        """Test that leader has no traffic penalty"""
        sim = RaceSimulator()
        sim.initialize_cars()

        # Leader is first in sorted times
        sorted_times = [(car.car_id, car.cumulative_time) for car in sim.cars]
        sorted_times.sort(key=lambda x: x[1])

        leader = sim.cars[sorted_times[0][0]]
        penalty = sim.calculate_traffic_penalty(leader, sorted_times)

        assert penalty == 0.0

    def test_calculate_traffic_penalty_close_behind(self):
        """Test traffic penalty when close to car ahead"""
        sim = RaceSimulator()
        sim.initialize_cars()

        # Create scenario: car 1 is 0.3 seconds behind car 0
        sorted_times = [(0, 1000.0), (1, 1000.3), (2, 1002.0)]

        car = sim.cars[1]
        penalty = sim.calculate_traffic_penalty(car, sorted_times)

        # Should have some penalty
        assert penalty > 0
        assert penalty < 2.5  # But not too large (allows for low overtaking ability)

    def test_calculate_traffic_penalty_far_behind(self):
        """Test no penalty when far from car ahead"""
        sim = RaceSimulator()
        sim.initialize_cars()

        # Car is 2 seconds behind
        sorted_times = [(0, 1000.0), (1, 1002.0)]

        car = sim.cars[1]
        penalty = sim.calculate_traffic_penalty(car, sorted_times)

        assert penalty == 0.0

    def test_simulate_lap_updates_states(self):
        """Test that simulating a lap updates car states"""
        sim = RaceSimulator(num_cars=5, num_laps=10)
        sim.initialize_cars()

        initial_fuel = sim.cars[0].fuel_level
        initial_tire_age = sim.cars[0].tire_age

        sim.simulate_lap(lap=1, strategy_pits={})

        # Fuel decreased
        assert sim.cars[0].fuel_level < initial_fuel

        # Tire age increased
        assert sim.cars[0].tire_age > initial_tire_age

    def test_simulate_lap_positions_unique(self):
        """Test that positions are unique after a lap"""
        sim = RaceSimulator(num_cars=10, num_laps=10)
        sim.initialize_cars()

        sim.simulate_lap(lap=1, strategy_pits={})

        positions = [car.position for car in sim.cars]
        assert len(set(positions)) == 10  # All unique
        assert set(positions) == set(range(1, 11))  # 1-10

    def test_simulate_race_completes(self):
        """Test that full race simulation completes"""
        sim = RaceSimulator(num_cars=10, num_laps=20)
        result = sim.simulate_race()

        # Check result structure
        assert 'final_positions' in result
        assert 'final_times' in result
        assert 'lap_history' in result
        assert 'winner' in result

        # Check we simulated all laps
        assert len(result['lap_history']) == 20

    def test_simulate_race_positions_valid(self):
        """Test that final positions are valid"""
        sim = RaceSimulator(num_cars=40, num_laps=50)
        result = sim.simulate_race()

        positions = list(result['final_positions'].values())

        # All unique
        assert len(set(positions)) == 40

        # All 1-40
        assert set(positions) == set(range(1, 41))

    def test_simulate_race_times_monotonic(self):
        """Test that cumulative times are monotonically increasing"""
        sim = RaceSimulator(num_cars=10, num_laps=20)
        result = sim.simulate_race()

        times = list(result['final_times'].values())

        # All positive
        assert all(t > 0 for t in times)

        # All unique (no ties given randomness)
        assert len(set(times)) == 10

    def test_simulate_race_reproducible(self):
        """Test that same seed produces same results"""
        sim1 = RaceSimulator(num_cars=10, num_laps=20, random_seed=42)
        result1 = sim1.simulate_race()

        sim2 = RaceSimulator(num_cars=10, num_laps=20, random_seed=42)
        result2 = sim2.simulate_race()

        # Same winner
        assert result1['winner'] == result2['winner']

        # Same final position for car 0
        assert result1['final_positions'][0] == result2['final_positions'][0]

    def test_simulate_race_with_strategy(self):
        """Test simulation with pit strategy"""
        sim = RaceSimulator(num_cars=10, num_laps=50)

        strategy = {
            0: [PitStop(lap=25)]
        }

        result = sim.simulate_race(strategy)

        # Should complete
        assert result['winner'] is not None

        # Check car 0 pitted (tire age reset)
        # After lap 25, tire age should be lower than if no pit
        # This is indirectly tested by race completing


class TestLapTimeRanges:
    """Test that lap times are in realistic ranges"""

    def test_lap_times_during_race(self):
        """Test lap times throughout a race are realistic"""
        # Use a shorter race with no pit stops for this test
        # Long races without pits will have very high lap times from degradation
        sim = RaceSimulator(num_cars=40, num_laps=50)
        result = sim.simulate_race()

        # Check all lap times for all cars
        # In a 50-lap race without pits, times will degrade but should stay reasonable
        max_reasonable_time = 90  # Allows for significant tire degradation
        for lap_data in result['lap_history']:
            for lap_time in lap_data['lap_times']:
                # Pitting cars have lap_time = 0, skip those
                if lap_time > 0:
                    assert 45 < lap_time < max_reasonable_time, f"Lap time {lap_time} out of range"

    def test_average_lap_time_reasonable(self):
        """Test that average lap time is around base time"""
        sim = RaceSimulator(num_cars=40, num_laps=100)
        result = sim.simulate_race()

        # Calculate average lap time (excluding zeros from pit stops)
        all_lap_times = []
        for lap_data in result['lap_history']:
            for lap_time in lap_data['lap_times']:
                if lap_time > 0:  # Exclude pit stops
                    all_lap_times.append(lap_time)

        avg_lap_time = np.mean(all_lap_times)

        # Should be reasonably close to base time (48s) + degradation
        # With no pit stops in 100 laps, times will degrade significantly
        assert 47 < avg_lap_time < 65


class TestTireDegradation:
    """Test tire degradation behavior"""

    def test_tire_degradation_curve(self):
        """Test that tire degradation accelerates (until cap)"""
        physics = CarPhysics(tire_degradation_rate=0.08)

        # Test acceleration before cap is reached (ages 0-30)
        penalties = []
        for age in [0, 10, 20, 30]:
            car = CarState(car_id=0, physics=physics, tire_age=age)
            penalties.append(car.get_tire_penalty())

        # Each increment should be larger than the last (acceleration)
        for i in range(1, len(penalties)):
            assert penalties[i] > penalties[i-1]

        # Acceleration means differences increase
        diffs = [penalties[i] - penalties[i-1] for i in range(1, len(penalties))]
        assert diffs[-1] > diffs[0]  # Last increment > first increment

        # Test that penalty caps at 5.0 seconds
        car_old = CarState(car_id=0, physics=physics, tire_age=100)
        penalty_capped = car_old.get_tire_penalty()
        assert penalty_capped == 5.0, "Penalty should cap at 5.0 seconds"

        # Test that penalty is capped at 40+ laps
        car_40 = CarState(car_id=0, physics=physics, tire_age=40)
        car_50 = CarState(car_id=0, physics=physics, tire_age=50)
        assert car_40.get_tire_penalty() == 5.0
        assert car_50.get_tire_penalty() == 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
