"""
Monte Carlo strategy evaluation engine.

Runs multiple race simulations in parallel to evaluate strategies
under uncertainty and variance.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from joblib import Parallel, delayed
from tqdm import tqdm
import pandas as pd

from src.simulator import RaceSimulator, PitStop
from src.strategy import Strategy


@dataclass
class SimulationResult:
    """
    Result from a single race simulation.

    Contains both final outcome and lap-by-lap history.
    """
    position: int  # Finishing position
    time: float  # Total race time
    winner: bool  # Whether our car won
    lap_times: List[float]  # Lap times for our car
    positions_over_time: List[int]  # Position each lap
    num_cautions: int  # Total cautions in race
    stage1_position: Optional[int] = None  # Position at end of stage 1
    stage2_position: Optional[int] = None  # Position at end of stage 2


def run_single_simulation(sim_config: Dict,
                         strategy: Strategy,
                         our_car_index: int,
                         random_seed: int,
                         mid_race_state: Optional[Dict] = None) -> SimulationResult:
    """
    Run a single race simulation with given strategy.

    Args:
        sim_config: Simulator configuration dict
        strategy: Strategy to apply to our car
        our_car_index: Which car (0-indexed) we're tracking
        random_seed: For reproducibility
        mid_race_state: Optional dict with mid-race state {
            'current_lap': int,
            'current_position': int,
            'tire_age': int,
            'fuel_level': float
        }

    Returns:
        SimulationResult with race outcome
    """
    # Create simulator with seed
    simulator = RaceSimulator(
        num_cars=sim_config['num_cars'],
        num_laps=sim_config['num_laps'],
        random_seed=random_seed
    )

    # Apply track-specific overrides if a track profile is specified
    base_lap_time = 48.0  # Default
    if 'track_profile' in sim_config:
        from config import TRACK_PROFILES
        track_key = sim_config['track_profile']
        if track_key in TRACK_PROFILES:
            tp = TRACK_PROFILES[track_key]
            simulator.config.base_lap_time = tp.base_lap_time
            simulator.config.tire_degradation_rate = tp.tire_degradation_rate
            simulator.config.caution_base_prob = tp.caution_base_prob
            simulator.config.traffic_penalty_factor = tp.traffic_penalty_factor
            simulator.config.min_lap_time = tp.base_lap_time - 3.0
            simulator.config.max_lap_time = tp.base_lap_time + 7.0
            simulator.track_length = tp.length_miles
            simulator.stage_laps = [tp.stage1_end, tp.stage2_end]
            base_lap_time = tp.base_lap_time

    # Set mid-race state if provided
    if mid_race_state:
        our_car_index = simulator.set_mid_race_state(
            our_car_index=our_car_index,
            current_lap=mid_race_state['current_lap'],
            our_position=mid_race_state['current_position'],
            our_tire_age=mid_race_state['tire_age'],
            our_fuel_level=mid_race_state['fuel_level'],
            base_lap_time=base_lap_time
        )

    # Convert Strategy to simulator's expected format
    # Simulator expects: Dict[car_id, List[PitStop]]
    # We only control our car (car_id = our_car_index)
    # Adjust pit laps if mid-race: convert from absolute lap to relative lap
    adjusted_pit_stops = []
    start_lap = mid_race_state['current_lap'] if mid_race_state else 0

    for pit in strategy.pit_stops:
        # Only include pit stops that are at or after the current lap
        if pit.lap >= start_lap:
            adjusted_pit_stops.append(pit)

    sim_strategy = {
        our_car_index: [
            PitStop(
                lap=pit.lap,
                duration=pit.duration,
                fuel_added=pit.fuel_added,
                tires_changed=pit.tires_changed
            )
            for pit in adjusted_pit_stops
        ]
    }

    # Run simulation (skip_init and set start_lap if mid-race state was set)
    start_lap = mid_race_state['current_lap'] + 1 if mid_race_state else 1
    result = simulator.simulate_race(
        strategy=sim_strategy,
        skip_init=mid_race_state is not None,
        start_lap=start_lap
    )

    # Extract our car's results
    our_position = result['final_positions'][our_car_index]
    our_time = result['final_times'][our_car_index]
    is_winner = result['winner'] == our_car_index

    # Extract lap history for our car
    lap_times = []
    positions_over_time = []
    for lap_data in result['lap_history']:
        lap_times.append(lap_data['lap_times'][our_car_index])
        positions_over_time.append(lap_data['positions'][our_car_index])

    # Count cautions
    num_cautions = sum(1 for lap_data in result['lap_history']
                      if lap_data.get('caution_active', False))

    # Extract stage positions if available
    stage1_position = None
    stage2_position = None
    if 'stage_positions' in result:
        if 1 in result['stage_positions'] and our_car_index in result['stage_positions'][1]:
            stage1_position = result['stage_positions'][1][our_car_index]
        if 2 in result['stage_positions'] and our_car_index in result['stage_positions'][2]:
            stage2_position = result['stage_positions'][2][our_car_index]

    return SimulationResult(
        position=our_position,
        time=our_time,
        winner=is_winner,
        lap_times=lap_times,
        positions_over_time=positions_over_time,
        num_cautions=num_cautions,
        stage1_position=stage1_position,
        stage2_position=stage2_position
    )


class MonteCarloEvaluator:
    """
    Parallel Monte Carlo strategy evaluator.

    Evaluates strategies by running many simulations with different
    random seeds to capture variance and uncertainty.
    """

    def __init__(self,
                 sim_config: Dict,
                 n_jobs: int = -1):
        """
        Initialize evaluator.

        Args:
            sim_config: Simulator configuration (num_cars, num_laps, etc.)
            n_jobs: Number of parallel jobs (-1 = all CPUs)
        """
        self.sim_config = sim_config
        self.n_jobs = n_jobs

    def evaluate_strategy(self,
                         strategy: Strategy,
                         num_simulations: int = 200,
                         our_car_index: int = 0,
                         show_progress: bool = True,
                         random_seed: Optional[int] = None,
                         mid_race_state: Optional[Dict] = None) -> Dict:
        """
        Evaluate a strategy via Monte Carlo simulation.

        Args:
            strategy: Strategy to evaluate
            num_simulations: Number of races to simulate
            our_car_index: Which car we're tracking (default: 0)
            show_progress: Show progress bar
            random_seed: Base seed for reproducibility
            mid_race_state: Optional dict with mid-race state {
                'current_lap': int,
                'current_position': int,
                'tire_age': int,
                'fuel_level': float
            }

        Returns:
            Dict with statistics and raw results
        """
        # Generate different seeds for each simulation
        rng = np.random.RandomState(random_seed)
        seeds = rng.randint(0, 2**31, size=num_simulations)

        # Run simulations in parallel
        results = Parallel(n_jobs=self.n_jobs)(
            delayed(run_single_simulation)(
                self.sim_config,
                strategy,
                our_car_index,
                seed,
                mid_race_state
            )
            for seed in tqdm(seeds, desc=f"Simulating {strategy.name}", disable=not show_progress)
        )

        # Extract metrics
        positions = [r.position for r in results]
        times = [r.time for r in results]
        wins = [r.winner for r in results]
        position_histories = [r.positions_over_time for r in results]

        # Calculate statistics
        metrics = {
            'mean_position': np.mean(positions),
            'median_position': np.median(positions),
            'std_position': np.std(positions),
            'min_position': np.min(positions),  # Best finish
            'max_position': np.max(positions),  # Worst finish
            'percentile_25': np.percentile(positions, 25),
            'percentile_75': np.percentile(positions, 75),
            'win_rate': np.mean(wins),
            'top5_rate': np.mean([p <= 5 for p in positions]),
            'top10_rate': np.mean([p <= 10 for p in positions]),
            'top20_rate': np.mean([p <= 20 for p in positions]),
            'mean_time': np.mean(times),
            'std_time': np.std(times),
            'positions': positions,  # Full distribution
            'position_histories': position_histories,  # For visualization
            'num_simulations': num_simulations
        }

        # Add probability distribution metrics
        metrics['position_distribution'] = {
            'percentiles': {p: np.percentile(positions, p) for p in [5, 10, 25, 50, 75, 90, 95]},
            'probability_top10': np.mean([p <= 10 for p in positions]),
            'probability_top5': np.mean([p <= 5 for p in positions]),
            'probability_win': np.mean([p == 1 for p in positions]),
            'probability_podium': np.mean([p <= 3 for p in positions])
        }

        # Calculate expected points if stage positions are available
        stage1_positions = [r.stage1_position for r in results if r.stage1_position is not None]
        stage2_positions = [r.stage2_position for r in results if r.stage2_position is not None]

        if stage1_positions or stage2_positions:
            from src.nascar_points import calculate_expected_points
            points_metrics = calculate_expected_points(
                stage1_positions=stage1_positions,
                stage2_positions=stage2_positions,
                final_positions=positions
            )
            metrics.update(points_metrics)

        return metrics

    def compare_strategies(self,
                          strategies: Dict[str, Strategy],
                          num_simulations: int = 200,
                          show_progress: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        Compare multiple strategies using Monte Carlo evaluation.

        Args:
            strategies: Dict of strategy name to Strategy
            num_simulations: Number of simulations per strategy
            show_progress: Show progress bars

        Returns:
            Tuple of (comparison DataFrame, detailed results dict)
        """
        results = {}

        for name, strategy in strategies.items():
            print(f"\nEvaluating: {name}")
            metrics = self.evaluate_strategy(
                strategy,
                num_simulations=num_simulations,
                show_progress=show_progress
            )
            results[name] = metrics

        # Create comparison DataFrame
        comparison_data = {}
        for name, metrics in results.items():
            comparison_data[name] = {
                'Avg Position': f"{metrics['mean_position']:.1f} ± {metrics['std_position']:.1f}",
                'Median': f"{metrics['median_position']:.1f}",
                'Win Rate': f"{metrics['win_rate']:.1%}",
                'Top-5': f"{metrics['top5_rate']:.1%}",
                'Top-10': f"{metrics['top10_rate']:.1%}",
                'Top-20': f"{metrics['top20_rate']:.1%}",
                'Best': metrics['min_position'],
                'Worst': metrics['max_position']
            }

        comparison_df = pd.DataFrame(comparison_data).T

        return comparison_df, results

    def find_best_strategy(self,
                          strategies: Dict[str, Strategy],
                          metric: str = 'mean_position',
                          num_simulations: int = 200) -> Tuple[str, Dict]:
        """
        Find the best strategy according to given metric.

        Args:
            strategies: Dict of strategies to compare
            metric: Metric to optimize ('mean_position', 'win_rate', etc.)
            num_simulations: Simulations per strategy

        Returns:
            Tuple of (best_strategy_name, best_metrics)
        """
        _, results = self.compare_strategies(
            strategies,
            num_simulations=num_simulations,
            show_progress=False
        )

        # Find best according to metric
        if metric in ['mean_position', 'median_position', 'std_position']:
            # Lower is better
            best_name = min(results.keys(), key=lambda k: results[k][metric])
        else:
            # Higher is better (win_rate, top5_rate, etc.)
            best_name = max(results.keys(), key=lambda k: results[k][metric])

        return best_name, results[best_name]


def calculate_statistical_significance(results_a: Dict,
                                     results_b: Dict) -> Dict:
    """
    Calculate statistical significance of difference between two strategies.

    Args:
        results_a: Metrics from strategy A
        results_b: Metrics from strategy B

    Returns:
        Dict with statistical test results
    """
    from scipy import stats

    positions_a = results_a['positions']
    positions_b = results_b['positions']

    # T-test (independent samples)
    t_stat, p_value = stats.ttest_ind(positions_a, positions_b)

    # Mann-Whitney U test (non-parametric)
    u_stat, u_p_value = stats.mannwhitneyu(positions_a, positions_b)

    # Effect size (Cohen's d)
    pooled_std = np.sqrt(
        (np.std(positions_a)**2 + np.std(positions_b)**2) / 2
    )
    cohens_d = (np.mean(positions_a) - np.mean(positions_b)) / pooled_std

    return {
        'mean_difference': np.mean(positions_a) - np.mean(positions_b),
        't_statistic': t_stat,
        'p_value': p_value,
        'mann_whitney_u': u_stat,
        'mann_whitney_p': u_p_value,
        'cohens_d': cohens_d,
        'significant': p_value < 0.05,
        'winner': 'A' if np.mean(positions_a) < np.mean(positions_b) else 'B'
    }


if __name__ == '__main__':
    # Test Monte Carlo engine
    import sys
    sys.path.insert(0, '.')
    from src.strategy import PRESET_STRATEGIES

    print("Testing Monte Carlo Engine")
    print("=" * 60)

    # Configuration
    sim_config = {
        'num_cars': 40,
        'num_laps': 100  # Shorter for testing
    }

    # Create evaluator
    evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)

    # Test single strategy
    print("\nEvaluating Standard strategy (20 simulations)...")
    metrics = evaluator.evaluate_strategy(
        PRESET_STRATEGIES['standard'],
        num_simulations=20,
        show_progress=True
    )

    print(f"\nResults:")
    print(f"  Mean Position: {metrics['mean_position']:.1f}")
    print(f"  Win Rate: {metrics['win_rate']:.1%}")
    print(f"  Top-10 Rate: {metrics['top10_rate']:.1%}")
