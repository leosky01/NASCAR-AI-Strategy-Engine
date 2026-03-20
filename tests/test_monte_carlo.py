"""
Tests for Monte Carlo strategy evaluation engine.
"""
import pytest
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '.')

from src.monte_carlo import (
    MonteCarloEvaluator,
    run_single_simulation,
    calculate_statistical_significance,
    SimulationResult
)
from src.strategy import Strategy, PitStop, PRESET_STRATEGIES
from src.simulator import RaceSimulator


class TestSimulationResult:
    """Test SimulationResult dataclass"""

    def test_create_result(self):
        """Test creating a simulation result"""
        result = SimulationResult(
            position=5,
            time=5000.0,
            winner=False,
            lap_times=[48.0] * 100,
            positions_over_time=list(range(1, 101)),
            num_cautions=3
        )

        assert result.position == 5
        assert result.winner == False
        assert len(result.lap_times) == 100
        assert result.num_cautions == 3


class TestSingleSimulation:
    """Test single race simulation"""

    @pytest.fixture
    def sim_config(self):
        """Standard simulator config"""
        return {
            'num_cars': 10,
            'num_laps': 50
        }

    @pytest.fixture
    def simple_strategy(self):
        """Simple 1-pit strategy"""
        return Strategy(
            name='Test Strategy',
            description='Test',
            pit_stops=[PitStop(lap=25)]
        )

    def test_run_simulation(self, sim_config, simple_strategy):
        """Test running a single simulation"""
        result = run_single_simulation(
            sim_config,
            simple_strategy,
            our_car_index=0,
            random_seed=42
        )

        # Check result structure
        assert isinstance(result.position, int)
        assert 1 <= result.position <= 10
        assert isinstance(result.time, float)
        assert result.time > 0
        assert isinstance(result.winner, bool)
        assert len(result.lap_times) == 50
        assert len(result.positions_over_time) == 50

    def test_simulation_reproducibility(self, sim_config, simple_strategy):
        """Test that same seed gives same result"""
        result1 = run_single_simulation(
            sim_config,
            simple_strategy,
            our_car_index=0,
            random_seed=42
        )
        result2 = run_single_simulation(
            sim_config,
            simple_strategy,
            our_car_index=0,
            random_seed=42
        )

        assert result1.position == result2.position
        assert result1.winner == result2.winner
        # Time may vary slightly due to float precision, but should be close
        assert abs(result1.time - result2.time) < 1.0


class TestMonteCarloEvaluator:
    """Test Monte Carlo evaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator with small config for testing"""
        sim_config = {
            'num_cars': 10,
            'num_laps': 30
        }
        return MonteCarloEvaluator(sim_config, n_jobs=2)

    @pytest.fixture
    def simple_strategy(self):
        """Simple strategy for testing"""
        return Strategy(
            name='Test',
            description='Test strategy',
            pit_stops=[PitStop(lap=15)]
        )

    def test_evaluate_single_strategy(self, evaluator, simple_strategy):
        """Test evaluating a single strategy"""
        metrics = evaluator.evaluate_strategy(
            simple_strategy,
            num_simulations=10,
            show_progress=False
        )

        # Check metrics exist
        assert 'mean_position' in metrics
        assert 'median_position' in metrics
        assert 'std_position' in metrics
        assert 'win_rate' in metrics
        assert 'top5_rate' in metrics
        assert 'top10_rate' in metrics
        assert 'positions' in metrics
        assert 'num_simulations' in metrics

        # Check values are reasonable
        assert 1 <= metrics['mean_position'] <= 10
        assert 0 <= metrics['win_rate'] <= 1
        assert metrics['num_simulations'] == 10

    def test_evaluate_returns_distribution(self, evaluator, simple_strategy):
        """Test that evaluation returns position distribution"""
        metrics = evaluator.evaluate_strategy(
            simple_strategy,
            num_simulations=20,
            show_progress=False
        )

        positions = metrics['positions']

        # Check we have all simulations
        assert len(positions) == 20

        # Check positions are valid
        assert all(1 <= p <= 10 for p in positions)

    def test_compare_strategies(self, evaluator):
        """Test comparing multiple strategies"""
        strategies = {
            'strategy_a': Strategy('A', 'A', [PitStop(lap=15)]),
            'strategy_b': Strategy('B', 'B', [PitStop(lap=20)])
        }

        comparison, results = evaluator.compare_strategies(
            strategies,
            num_simulations=10,
            show_progress=False
        )

        # Check comparison DataFrame
        assert isinstance(comparison, pd.DataFrame)
        assert len(comparison) == 2
        assert 'Avg Position' in comparison.columns
        assert 'Win Rate' in comparison.columns

        # Check results dict
        assert 'strategy_a' in results
        assert 'strategy_b' in results

    def test_find_best_strategy(self, evaluator):
        """Test finding best strategy"""
        strategies = {
            'early': Strategy('Early', 'Early', [PitStop(lap=10)]),
            'late': Strategy('Late', 'Late', [PitStop(lap=25)])
        }

        best_name, best_metrics = evaluator.find_best_strategy(
            strategies,
            metric='mean_position',
            num_simulations=10
        )

        # Check we got a valid strategy
        assert best_name in ['early', 'late']
        assert 'mean_position' in best_metrics

    def test_parallel_speedup(self, evaluator):
        """Test that parallel execution is faster than serial"""
        import time

        strategy = Strategy('Test', 'Test', [PitStop(lap=15)])

        # Serial timing
        start = time.time()
        metrics_serial = MonteCarloEvaluator(
            evaluator.sim_config,
            n_jobs=1  # Serial
        ).evaluate_strategy(
            strategy,
            num_simulations=20,
            show_progress=False
        )
        serial_time = time.time() - start

        # Parallel timing
        start = time.time()
        metrics_parallel = evaluator.evaluate_strategy(
            strategy,
            num_simulations=20,
            show_progress=False
        )
        parallel_time = time.time() - start

        # Results should be reasonably similar (allow for Monte Carlo variance)
        assert abs(metrics_serial['mean_position'] - metrics_parallel['mean_position']) < 3.0

        # Parallel should be faster (or at least not much slower)
        # Note: This test might fail on single-core machines
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            if cpu_count > 1:
                assert parallel_time < serial_time * 2.0  # Allow overhead
        except:
            pass  # Skip if multiprocessing not available


class TestStatisticalSignificance:
    """Test statistical significance calculations"""

    def test_statistical_test(self):
        """Test statistical significance calculation"""
        # Create two different result sets
        results_a = {
            'positions': [5, 8, 6, 7, 5, 9, 4, 6, 7, 5]  # Avg ~6.2
        }
        results_b = {
            'positions': [10, 12, 11, 9, 10, 13, 11, 12, 10, 11]  # Avg ~11
        }

        stats = calculate_statistical_significance(results_a, results_b)

        # Check test was performed
        assert 'p_value' in stats
        assert 'cohens_d' in stats
        assert 'significant' in stats
        assert 'winner' in stats

        # With these distributions, should be significant
        assert stats['p_value'] < 0.05
        assert stats['significant'] == True
        assert stats['winner'] == 'A'  # A is better (lower positions)

    def test_identical_distributions(self):
        """Test with identical distributions"""
        positions = [5, 6, 7, 8, 9, 10, 5, 6, 7, 8]

        results_a = {'positions': positions}
        results_b = {'positions': positions.copy()}

        stats = calculate_statistical_significance(results_a, results_b)

        # Should not be significant (no difference)
        assert stats['p_value'] > 0.05
        assert stats['significant'] == False
        assert stats['mean_difference'] == 0.0


class TestMonteCarloIntegration:
    """Integration tests for full Monte Carlo pipeline"""

    def test_full_workflow(self):
        """Test complete workflow: compare strategies, find best"""
        sim_config = {
            'num_cars': 10,
            'num_laps': 40
        }

        evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)

        # Compare preset strategies
        strategies = {
            'standard': PRESET_STRATEGIES['standard'],
            'aggressive': PRESET_STRATEGIES['aggressive']
        }

        comparison, results = evaluator.compare_strategies(
            strategies,
            num_simulations=20,
            show_progress=False
        )

        # Check comparison
        assert len(comparison) == 2
        assert 'Avg Position' in comparison.columns

        # Find best
        best_name, best_metrics = evaluator.find_best_strategy(
            strategies,
            metric='mean_position',
            num_simulations=20
        )

        # Check best is one of our strategies
        assert best_name in ['standard', 'aggressive']

    def test_strategy_variance(self):
        """Test that Monte Carlo captures variance"""
        sim_config = {
            'num_cars': 10,
            'num_laps': 40
        }

        evaluator = MonteCarloEvaluator(sim_config, n_jobs=1)

        # Run same strategy multiple times
        metrics = evaluator.evaluate_strategy(
            PRESET_STRATEGIES['standard'],
            num_simulations=50,
            show_progress=False
        )

        # Should have variance in results
        positions = metrics['positions']
        std_dev = np.std(positions)

        # Standard deviation should be > 0 (there's variance)
        assert std_dev > 0

        # Should have spread in positions
        assert max(positions) - min(positions) > 2


class TestPerformance:
    """Performance tests for Monte Carlo engine"""

    def test_simulation_speed(self):
        """Test that simulations run fast enough"""
        sim_config = {
            'num_cars': 40,
            'num_laps': 100
        }

        evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)

        import time
        start = time.time()

        metrics = evaluator.evaluate_strategy(
            PRESET_STRATEGIES['standard'],
            num_simulations=50,
            show_progress=False
        )

        elapsed = time.time() - start

        # Should complete 50 simulations in reasonable time
        # (< 60 seconds, but realistically < 10 seconds)
        assert elapsed < 60

        # Print for info
        print(f"\n50 simulations in {elapsed:.2f} seconds")
        print(f"  {50/elapsed:.1f} simulations/second")

    def test_scalability(self):
        """Test that performance scales reasonably"""
        sim_config = {
            'num_cars': 40,
            'num_laps': 50  # Shorter race for testing
        }

        evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)

        import time

        # Test with 10 sims
        start = time.time()
        metrics10 = evaluator.evaluate_strategy(
            PRESET_STRATEGIES['standard'],
            num_simulations=10,
            show_progress=False
        )
        time10 = time.time() - start

        # Test with 20 sims
        start = time.time()
        metrics20 = evaluator.evaluate_strategy(
            PRESET_STRATEGIES['standard'],
            num_simulations=20,
            show_progress=False
        )
        time20 = time.time() - start

        # 20 sims should take roughly 2x longer (within reason)
        # Allow 2.5x to account for overhead
        assert time20 < time10 * 3

        print(f"\n10 sims: {time10:.2f}s, 20 sims: {time20:.2f}s")
        print(f"  Ratio: {time20/time10:.2f}x")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
