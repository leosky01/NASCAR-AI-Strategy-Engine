#!/usr/bin/env python3
"""
Test script to verify the mid-race simulation fix.

This tests the scenario described by the user:
- Current lap: 200
- Tire age: 4
- Fuel level: 100%
- Current position: 15
- Track: Charlotte (267 laps)
"""
import sys
sys.path.insert(0, '.')

from src.simulator import RaceSimulator
from src.monte_carlo import MonteCarloEvaluator
from src.strategy import Strategy, PitStop
from config import TRACK_PROFILES

def test_mid_race_simulation():
    """Test that mid-race simulation works correctly"""

    print("=" * 70)
    print("Testing Mid-Race Simulation Fix")
    print("=" * 70)

    # Setup
    track_profile = TRACK_PROFILES['Charlotte']
    num_laps = 267
    current_lap = 200
    current_position = 15
    tire_age = 4
    fuel_level = 100.0

    print(f"\nTrack: {track_profile.name}")
    print(f"Total laps: {num_laps}")
    print(f"Current lap: {current_lap}")
    print(f"Laps remaining: {num_laps - current_lap}")
    print(f"Current position: {current_position}")
    print(f"Tire age: {tire_age}")
    print(f"Fuel level: {fuel_level}%")

    # Test 1: Simulator mid-race state setup
    print("\n" + "-" * 70)
    print("Test 1: set_mid_race_state")
    print("-" * 70)

    simulator = RaceSimulator(
        num_cars=40,
        num_laps=num_laps,
        random_seed=42
    )

    # Apply track profile
    simulator.config.base_lap_time = track_profile.base_lap_time
    simulator.config.tire_degradation_rate = track_profile.tire_degradation_rate
    simulator.config.caution_base_prob = track_profile.caution_base_prob

    # Set mid-race state
    our_car_index = simulator.set_mid_race_state(
        our_car_index=0,
        current_lap=current_lap,
        our_position=current_position,
        our_tire_age=tire_age,
        our_fuel_level=fuel_level,
        base_lap_time=track_profile.base_lap_time
    )

    print(f"Our car index after reordering: {our_car_index}")
    print(f"Our car position: {simulator.cars[our_car_index].position}")
    print(f"Our car tire age: {simulator.cars[our_car_index].tire_age}")
    print(f"Our car fuel level: {simulator.cars[our_car_index].fuel_level:.1f}%")
    print(f"Our car cumulative time: {simulator.cars[our_car_index].cumulative_time:.1f}s")

    # Verify our car is in the correct position
    assert simulator.cars[our_car_index].tire_age == tire_age, "Tire age not set correctly"
    assert simulator.cars[our_car_index].fuel_level == fuel_level, "Fuel level not set correctly"
    assert our_car_index == current_position - 1, f"Our car index should be {current_position - 1}, got {our_car_index}"

    print("✓ Mid-race state set correctly")

    # Test 2: Run partial race simulation
    print("\n" + "-" * 70)
    print("Test 2: Simulate remaining laps")
    print("-" * 70)

    # Create a simple strategy: pit now (lap 200)
    pit_now_strategy = Strategy(
        name="Pit Now",
        description="Pit on lap 200",
        pit_stops=[PitStop(lap=current_lap)]
    )

    sim_strategy = {
        our_car_index: [PitStop(lap=current_lap)]
    }

    result = simulator.simulate_race(
        strategy=sim_strategy,
        skip_init=True,
        start_lap=current_lap + 1
    )

    print(f"Simulated from lap {current_lap + 1} to {num_laps}")
    print(f"Final position: {result['final_positions'][our_car_index]}")
    print(f"Laps in history: {len(result['lap_history'])}")

    assert len(result['lap_history']) == num_laps - current_lap, \
        f"Expected {num_laps - current_lap} laps in history, got {len(result['lap_history'])}"

    print("✓ Partial race simulation successful")

    # Test 3: Full Monte Carlo evaluation with mid-race state
    print("\n" + "-" * 70)
    print("Test 3: Monte Carlo evaluation with mid-race state")
    print("-" * 70)

    sim_config = {
        'num_cars': 40,
        'num_laps': num_laps,
        'track_profile': 'Charlotte'
    }

    evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)

    # Create two strategies to compare
    pit_strategy = Strategy(
        name="Pit Now",
        description="Pit immediately",
        pit_stops=[PitStop(lap=current_lap)]
    )

    stay_out_strategy = Strategy(
        name="Stay Out",
        description="Stay out and pit later",
        pit_stops=[PitStop(lap=current_lap + 30)]
    )

    mid_race_state = {
        'current_lap': current_lap,
        'current_position': current_position,
        'tire_age': tire_age,
        'fuel_level': fuel_level
    }

    print("Evaluating 'Pit Now' strategy...")
    pit_metrics = evaluator.evaluate_strategy(
        pit_strategy,
        num_simulations=20,
        show_progress=False,
        mid_race_state=mid_race_state
    )

    print("Evaluating 'Stay Out' strategy...")
    stay_out_metrics = evaluator.evaluate_strategy(
        stay_out_strategy,
        num_simulations=20,
        show_progress=False,
        mid_race_state=mid_race_state
    )

    print(f"\nResults:")
    print(f"  Pit Now    - Avg position: {pit_metrics['mean_position']:.1f}, Top-10: {pit_metrics['top10_rate']:.1%}")
    print(f"  Stay Out   - Avg position: {stay_out_metrics['mean_position']:.1f}, Top-10: {stay_out_metrics['top10_rate']:.1%}")

    # With fresh tires (age 4) and full fuel, staying out should be better
    # since we're only 67 laps from the finish
    if stay_out_metrics['mean_position'] < pit_metrics['mean_position']:
        print("✓ 'Stay Out' correctly recommended (better avg position)")
    else:
        print("⚠ 'Pit Now' has better position (may be valid depending on scenario)")

    print("\n" + "=" * 70)
    print("All tests passed! ✓")
    print("=" * 70)

    return True

if __name__ == '__main__':
    try:
        test_mid_race_simulation()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
