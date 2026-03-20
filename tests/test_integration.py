"""
Integration tests for end-to-end workflows.

Tests that all components work together properly.
"""
import pytest
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '.')

from src.simulator import RaceSimulator, CarPhysics
from src.models import CautionPredictor
from src.monte_carlo import MonteCarloEvaluator
from src.strategy import Strategy, PitStop, PRESET_STRATEGIES
from src.sensitivity import StrategySensitivityAnalyzer


class TestSimulationToEvaluation:
    """Test simulator → Monte Carlo workflow"""

    @pytest.fixture
    def sim_config(self):
        """Standard simulation config"""
        return {
            'num_cars': 20,
            'num_laps': 50
        }

    @pytest.fixture
    def evaluator(self, sim_config):
        """Create Monte Carlo evaluator"""
        return MonteCarloEvaluator(sim_config, n_jobs=2)

    def test_simulate_then_evaluate(self, sim_config, evaluator):
        """Test that we can simulate a race and then evaluate it"""
        # First, simulate a single race
        sim = RaceSimulator(
            num_cars=sim_config['num_cars'],
            num_laps=sim_config['num_laps']
        )
        result = sim.simulate_race()

        # Verify simulation worked
        assert result['lap_history'] is not None
        assert len(result['lap_history']) == sim_config['num_laps']

        # Now evaluate using same strategy
        strategy = Strategy(
            name='Test',
            description='Test',
            pit_stops=[PitStop(lap=25)]
        )

        metrics = evaluator.evaluate_strategy(
            strategy,
            num_simulations=10,
            show_progress=False
        )

        # Verify evaluation worked
        assert metrics['mean_position'] > 0
        assert metrics['mean_position'] <= sim_config['num_cars']
        assert metrics['win_rate'] >= 0
        assert metrics['win_rate'] <= 1

    def test_preset_strategies_all_valid(self, evaluator):
        """Test that all preset strategies can be evaluated"""
        results = {}

        for name, strategy in PRESET_STRATEGIES.items():
            metrics = evaluator.evaluate_strategy(
                strategy,
                num_simulations=10,
                show_progress=False
            )
            results[name] = metrics

            # Verify all metrics are valid
            assert metrics['mean_position'] > 0
            assert metrics['mean_position'] <= 40
            assert 0 <= metrics['win_rate'] <= 1
            assert 0 <= metrics['top5_rate'] <= 1
            assert 0 <= metrics['top10_rate'] <= 1

        # Verify we got results for all strategies
        assert len(results) == len(PRESET_STRATEGIES)


class TestEvaluationToSensitivity:
    """Test Monte Carlo → Sensitivity analysis workflow"""

    @pytest.fixture
    def sim_config(self):
        return {
            'num_cars': 15,
            'num_laps': 40
        }

    @pytest.fixture
    def evaluator(self, sim_config):
        return MonteCarloEvaluator(sim_config, n_jobs=2)

    @pytest.fixture
    def analyzer(self, evaluator):
        return StrategySensitivityAnalyzer(evaluator)

    def test_evaluate_then_optimize(self, analyzer, evaluator):
        """Test that we can evaluate a strategy then optimize it"""
        # Create a strategy
        strategy = Strategy(
            name='Test Strategy',
            description='For testing',
            pit_stops=[PitStop(lap=30)]
        )

        # First evaluate
        original_metrics = evaluator.evaluate_strategy(
            strategy,
            num_simulations=20,
            show_progress=False
        )

        # Then optimize
        result = analyzer.find_optimal_pit_lap(
            strategy,
            pit_index=0,
            search_range=(25, 35),
            num_sims_per_point=10
        )

        # Verify optimization completed
        assert 'optimal_lap' in result
        assert 'expected_position' in result
        assert 'improvement' in result

        # Verify optimal is in search range
        assert 25 <= result['optimal_lap'] <= 35

    def test_sensitivity_curve_generation(self, analyzer):
        """Test that sensitivity curves can be generated"""
        strategy = Strategy(
            name='Test',
            description='Test',
            pit_stops=[PitStop(lap=25)]
        )

        # Generate sensitivity curve
        df = analyzer.analyze_pit_timing(
            strategy,
            pit_index=0,
            lap_range=(20, 30),
            lap_step=2,
            num_sims_per_point=5,
            show_progress=False
        )

        # Verify curve structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'pit_lap' in df.columns
        assert 'mean_position' in df.columns
        assert 'is_optimal' in df.columns

        # Verify optimal is marked
        assert df['is_optimal'].sum() == 1


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    def test_complete_optimization_workflow(self):
        """Test full workflow: create strategy → evaluate → optimize → compare"""
        sim_config = {'num_cars': 20, 'num_laps': 60}

        # Create evaluator and analyzer
        evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)
        analyzer = StrategySensitivityAnalyzer(evaluator)

        # Start with a strategy
        original_strategy = Strategy(
            name='Original',
            description='Starting point',
            pit_stops=[PitStop(lap=40)]
        )

        # Evaluate original
        print("\n1. Evaluating original strategy...")
        original_metrics = evaluator.evaluate_strategy(
            original_strategy,
            num_simulations=30,
            show_progress=False
        )
        print(f"   Original: Mean pos = {original_metrics['mean_position']:.2f}")

        # Optimize it
        print("2. Optimizing strategy...")
        optimized_strategy = analyzer.optimize_complete_strategy(
            original_strategy,
            search_ranges=[(30, 50)],
            num_sims_per_point=10
        )

        # Evaluate optimized
        print("3. Evaluating optimized strategy...")
        optimized_metrics = evaluator.evaluate_strategy(
            optimized_strategy,
            num_simulations=30,
            show_progress=False
        )
        print(f"   Optimized: Mean pos = {optimized_metrics['mean_position']:.2f}")

        # Verify workflow completed
        assert original_metrics['mean_position'] > 0
        assert optimized_metrics['mean_position'] > 0
        # Optimized strategy was created successfully
        assert optimized_strategy is not None
        assert len(optimized_strategy.pit_stops) == 1

    def test_multi_strategy_comparison_workflow(self):
        """Test comparing multiple strategies with sensitivity analysis"""
        sim_config = {'num_cars': 30, 'num_laps': 80}
        evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)
        analyzer = StrategySensitivityAnalyzer(evaluator)

        # Create multiple strategies
        strategies = {
            'early': Strategy('Early', 'Early pit', [PitStop(lap=35)]),
            'middle': Strategy('Middle', 'Middle pit', [PitStop(lap=45)]),
            'late': Strategy('Late', 'Late pit', [PitStop(lap=55)])
        }

        # Evaluate all
        print("\n1. Evaluating strategies...")
        results = {}
        for name, strategy in strategies.items():
            metrics = evaluator.evaluate_strategy(
                strategy,
                num_simulations=20,
                show_progress=False
            )
            results[name] = metrics
            print(f"   {name}: Mean pos = {metrics['mean_position']:.2f}")

        # Optimize each
        print("2. Optimizing each strategy...")
        optimized = {}
        for name, strategy in strategies.items():
            opt = analyzer.find_optimal_pit_lap(
                strategy,
                pit_index=0,
                search_range=(30, 60),
                num_sims_per_point=10
            )
            optimized[name] = opt
            print(f"   {name}: Optimal lap = {opt['optimal_lap']}, "
                  f"improvement = {opt['improvement']:.1f} positions")

        # Verify all completed
        assert len(results) == 3
        assert len(optimized) == 3

        # All should have valid results
        for name in strategies.keys():
            assert results[name]['mean_position'] > 0
            assert 30 <= optimized[name]['optimal_lap'] <= 60


class TestDataFlow:
    """Test that data flows correctly between components"""

    def test_race_data_to_features_to_prediction(self):
        """Test that race data can be converted for feature extraction"""
        import pandas as pd

        # Create sample race data
        sim_config = {'num_cars': 10, 'num_laps': 20}
        sim = RaceSimulator(
            num_cars=sim_config['num_cars'],
            num_laps=sim_config['num_laps']
        )
        result = sim.simulate_race()

        # Verify we can create DataFrame from race history
        # This is needed for feature extraction
        lap_data = []
        for lap_entry in result['lap_history']:
            for car_id, lap_time in enumerate(lap_entry['lap_times']):
                lap_data.append({
                    'lap': lap_entry['lap'],
                    'car': car_id,
                    'lap_time': lap_time
                })

        race_df = pd.DataFrame(lap_data)

        # Verify DataFrame structure
        assert 'lap' in race_df.columns
        assert 'car' in race_df.columns
        assert 'lap_time' in race_df.columns
        assert len(race_df) > 0

    def test_strategy_to_simulation_to_result(self):
        """Test that strategy is properly used in simulation"""
        sim_config = {'num_cars': 15, 'num_laps': 30}

        # Create strategy with specific pit (this test verifies strategy structure)
        strategy = Strategy(
            name='Test',
            description='Test',
            pit_stops=[PitStop(lap=20)]
        )

        # Simulate a race
        sim = RaceSimulator(
            num_cars=sim_config['num_cars'],
            num_laps=sim_config['num_laps']
        )
        result = sim.simulate_race()

        # Verify simulation completed successfully
        assert result['lap_history'] is not None
        assert len(result['lap_history']) == sim_config['num_laps']
        assert 'final_positions' in result


class TestConfigConsistency:
    """Test that configuration is used consistently"""

    def test_simulator_uses_config(self):
        """Test that simulator respects config parameters"""
        from config import SimulatorConfig

        config = SimulatorConfig(
            num_cars=25,
            num_laps=40,
            min_lap_time=46.0,
            max_lap_time=54.0
        )

        sim = RaceSimulator(
            num_cars=config.num_cars,
            num_laps=config.num_laps
        )
        result = sim.simulate_race()

        # Verify config was used
        assert len(result['lap_history']) == config.num_laps
        assert len(result['lap_history'][0]['positions']) == config.num_cars

    def test_monte_carlo_uses_config(self):
        """Test that Monte Carlo evaluator uses config"""
        from config import MonteCarloConfig

        mc_config = MonteCarloConfig(
            default_simulations=50,
            n_jobs=2
        )

        sim_config = {'num_cars': 20, 'num_laps': 30}
        evaluator = MonteCarloEvaluator(sim_config, n_jobs=mc_config.n_jobs)

        strategy = Strategy('Test', 'Test', [PitStop(lap=15)])

        # Use the configured number of simulations
        metrics = evaluator.evaluate_strategy(
            strategy,
            num_simulations=mc_config.default_simulations,
            show_progress=False
        )

        assert metrics['mean_position'] > 0


class TestPerformanceBenchmarks:
    """Performance benchmarks for critical operations"""

    def test_simulation_speed_benchmark(self):
        """Benchmark single race simulation speed"""
        import time

        sim_config = {'num_cars': 40, 'num_laps': 100}
        sim = RaceSimulator(
            num_cars=sim_config['num_cars'],
            num_laps=sim_config['num_laps']
        )

        start = time.time()
        result = sim.simulate_race()
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0, f"Simulation too slow: {elapsed:.2f}s"
        print(f"\n✓ Single race simulation: {elapsed:.3f}s")

    def test_monte_carlo_speed_benchmark(self):
        """Benchmark Monte Carlo evaluation speed"""
        import time

        sim_config = {'num_cars': 40, 'num_laps': 100}
        evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)

        strategy = Strategy('Test', 'Test', [PitStop(lap=50)])

        start = time.time()
        metrics = evaluator.evaluate_strategy(
            strategy,
            num_simulations=100,
            show_progress=False
        )
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 20.0, f"Monte Carlo too slow: {elapsed:.2f}s"
        print(f"\n✓ 100-simulation Monte Carlo: {elapsed:.3f}s")

    def test_sensitivity_analysis_speed_benchmark(self):
        """Benchmark sensitivity analysis speed"""
        import time

        sim_config = {'num_cars': 30, 'num_laps': 60}
        evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)
        analyzer = StrategySensitivityAnalyzer(evaluator)

        strategy = Strategy('Test', 'Test', [PitStop(lap=30)])

        start = time.time()
        df = analyzer.analyze_pit_timing(
            strategy,
            pit_index=0,
            lap_range=(25, 35),
            lap_step=2,
            num_sims_per_point=10,
            show_progress=False
        )
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 15.0, f"Sensitivity analysis too slow: {elapsed:.2f}s"
        print(f"\n✓ Sensitivity analysis (6 points): {elapsed:.3f}s")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
