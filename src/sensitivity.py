"""
Sensitivity analysis for NASCAR strategy optimization.

Analyzes how changing pit stop timing affects expected finishing position.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy.optimize import minimize_scalar
from dataclasses import dataclass

from src.monte_carlo import MonteCarloEvaluator, SimulationResult
from src.strategy import Strategy, PitStop
from src.simulator import RaceSimulator
from config import SensitivityConfig


@dataclass
class SensitivityResult:
    """Results from sensitivity analysis on a single pit stop"""
    pit_lap: int
    mean_position: float
    std_position: float
    win_rate: float
    top5_rate: float
    top10_rate: float
    position_distribution: List[int]
    samples: int


class StrategySensitivityAnalyzer:
    """
    Analyzes strategy sensitivity to pit stop timing.

    Answers questions like:
    - What's the optimal lap for pit stop #2?
    - How much does pit timing matter?
    - What's the risk/reward tradeoff?
    """

    def __init__(self, mc_evaluator: MonteCarloEvaluator,
                 config: SensitivityConfig = None):
        """
        Initialize analyzer.

        Args:
            mc_evaluator: MonteCarloEvaluator instance
            config: Optional SensitivityConfig, uses defaults if None
        """
        self.mc_evaluator = mc_evaluator
        self.config = config or SensitivityConfig()

    def analyze_pit_timing(self,
                           base_strategy: Strategy,
                           pit_index: int,
                           lap_range: Tuple[int, int],
                           lap_step: int = 2,
                           num_sims_per_point: int = 50,
                           show_progress: bool = False) -> pd.DataFrame:
        """
        Analyze sensitivity of a specific pit stop timing.

        Varies the pit lap and evaluates expected finishing position.

        Args:
            base_strategy: Original strategy to analyze
            pit_index: Which pit stop to vary (0-indexed)
            lap_range: (min_lap, max_lap) to test
            lap_step: Step size for lap variation
            num_sims_per_point: Simulations per lap (lower for speed)
            show_progress: Show progress bar

        Returns:
            DataFrame with sensitivity analysis results
        """
        # Get the original pit stop we're varying
        if pit_index >= len(base_strategy.pit_stops):
            raise ValueError(f"Pit index {pit_index} out of range")

        original_pit = base_strategy.pit_stops[pit_index]

        print(f"\nAnalyzing pit stop #{pit_index + 1} (originally lap {original_pit.lap})")
        print(f"Testing range: laps {lap_range[0]} to {lap_range[1]}")

        results = []

        # Test each pit lap
        for test_lap in range(lap_range[0], lap_range[1] + 1, lap_step):
            # Create modified strategy with this pit timing
            modified_strategy = self._create_modified_strategy(
                base_strategy,
                pit_index,
                test_lap
            )

            # Evaluate this variant
            print(f"  Testing pit at lap {test_lap}...")
            metrics = self.mc_evaluator.evaluate_strategy(
                modified_strategy,
                num_simulations=num_sims_per_point,
                show_progress=False
            )

            results.append({
                'pit_lap': test_lap,
                'mean_position': metrics['mean_position'],
                'std_position': metrics['std_position'],
                'win_rate': metrics['win_rate'],
                'top5_rate': metrics['top5_rate'],
                'top10_rate': metrics['top10_rate'],
                'min_position': metrics['min_position'],
                'max_position': metrics['max_position'],
                'percentile_25': metrics['percentile_25'],
                'percentile_75': metrics['percentile_75']
            })

        df = pd.DataFrame(results)

        # Find optimal lap
        best_idx = df['mean_position'].idxmin()
        best_lap = df.loc[best_idx, 'pit_lap']
        best_mean = df.loc[best_idx, 'mean_position']

        # Mark optimal in DataFrame
        df['is_optimal'] = df['pit_lap'] == best_lap

        print(f"\n✓ Optimal lap: {best_lap}")
        print(f"  Expected position: {best_mean:.2f}")
        print(f"  Improvement vs original: {original_pit.lap - best_lap:.1f} positions")

        return df

    def find_optimal_pit_lap(self,
                           base_strategy: Strategy,
                           pit_index: int,
                           search_range: Tuple[int, int] = (30, 80),
                           num_sims_per_point: int = 30) -> Dict:
        """
        Find optimal pit lap using efficient optimization.

        Uses scipy.optimize.minimize_scalar for faster optimization
        than grid search.

        Args:
            base_strategy: Strategy to optimize
            pit_index: Which pit stop to optimize
            search_range: (min_lap, max_lap) to search
            num_sims_per_point: Simulations per evaluation

        Returns:
            Dict with optimal_lap, expected_position, and improvement
        """
        if pit_index >= len(base_strategy.pit_stops):
            raise ValueError(f"Pit index {pit_index} out of range")

        original_lap = base_strategy.pit_stops[pit_index].lap
        original_position = self._evaluate_single_timing(
            base_strategy, pit_index, original_lap, num_sims_per_point
        )

        print(f"\nFinding optimal pit for stop #{pit_index + 1}...")
        print(f"Original: lap {original_lap}, expected position {original_position:.2f}")

        def objective_function(lap):
            """Objective to minimize (expected finishing position)"""
            # Ensure lap is integer
            lap_int = int(round(lap))

            # Skip if same as original (no need to re-evaluate)
            if lap_int == original_lap:
                return original_position

            # Create modified strategy
            modified_strategy = self._create_modified_strategy(
                base_strategy,
                pit_index,
                lap_int
            )

            # Evaluate
            metrics = self.mc_evaluator.evaluate_strategy(
                modified_strategy,
                num_simulations=num_sims_per_point,
                show_progress=False
            )

            return metrics['mean_position']

        # Optimize
        print("  Optimizing...")
        result = minimize_scalar(
            objective_function,
            bounds=search_range,
            method='bounded',
            options={'xatol': self.config.optimization_tolerance}
        )

        optimal_lap = int(round(result.x))
        expected_position = result.fun

        # Evaluate optimal to confirm
        final_metrics = self._evaluate_single_timing(
            base_strategy, pit_index, optimal_lap, num_sims_per_point
        )

        improvement = original_position - expected_position

        return {
            'pit_index': pit_index,
            'original_lap': original_lap,
            'original_position': original_position,
            'optimal_lap': optimal_lap,
            'expected_position': expected_position,
            'improvement': improvement,
            'improvement_pct': (improvement / original_position) * 100,
            'final_metrics': final_metrics
        }

    def optimize_complete_strategy(self,
                                  base_strategy: Strategy,
                                  search_ranges: List[Tuple[int, int]],
                                  num_sims_per_point: int = 50) -> Strategy:
        """
        Optimize all pit stops in a strategy.

        Args:
            base_strategy: Strategy to optimize
            search_ranges: List of (min_lap, max_lap) for each pit
            num_sims_per_point: Simulations per evaluation

        Returns:
            Optimized Strategy with improved pit timings
        """
        print(f"\n" + "=" * 60)
        print(f"OPTIMIZING STRATEGY: {base_strategy.name}")
        print("=" * 60)

        optimized_pits = []

        for i, (original_pit, search_range) in enumerate(zip(
            base_strategy.pit_stops,
            search_ranges
        )):
            print(f"\nPit Stop #{i + 1} (original: lap {original_pit.lap})")

            result = self.find_optimal_pit_lap(
                base_strategy,
                pit_index=i,
                search_range=search_range,
                num_sims_per_point=num_sims_per_point
            )

            optimized_pits.append(PitStop(
                lap=result['optimal_lap'],
                duration=original_pit.duration,
                fuel_added=original_pit.fuel_added,
                tires_changed=original_pit.tires_changed
            ))

            print(f"  Original: lap {result['original_lap']}, pos {result['original_position']:.2f}")
            print(f"  Optimal:  lap {result['optimal_lap']}, pos {result['expected_position']:.2f}")
            print(f"  Improvement: {result['improvement']:.1f} positions ({result['improvement_pct']:.1f}%)")

        # Create optimized strategy
        optimized_strategy = Strategy(
            name=f"Optimized {base_strategy.name}",
            description=f"Optimized version of {base_strategy.name}",
            pit_stops=optimized_pits
        )

        # Compare original vs optimized
        print(f"\n" + "=" * 60)
        print("COMPARISON")
        print("=" * 60)

        original_metrics = self.mc_evaluator.evaluate_strategy(
            base_strategy,
            num_simulations=100,
            show_progress=False
        )

        optimized_metrics = self.mc_evaluator.evaluate_strategy(
            optimized_strategy,
            num_simulations=100,
            show_progress=False
        )

        print(f"Original: Mean pos = {original_metrics['mean_position']:.2f}, Win rate = {original_metrics['win_rate']:.1%}")
        print(f"Optimized: Mean pos = {optimized_metrics['mean_position']:.2f}, Win rate = {optimized_metrics['win_rate']:.1%}")
        print(f"Improvement: {original_metrics['mean_position'] - optimized_metrics['mean_position']:.2f} positions")

        return optimized_strategy

    def generate_sensitivity_report(self,
                                   strategies: Dict[str, Strategy],
                                   num_sims_per_point: int = 30) -> Dict:
        """
        Generate comprehensive sensitivity report for all strategies.

        Args:
            strategies: Dict of strategies to analyze
            num_sims_per_point: Simulations per evaluation

        Returns:
            Dict with sensitivity analysis for each strategy/pit
        """
        report = {}

        for strat_name, strategy in strategies.items():
            print(f"\n{'=' * 60}")
            print(f"Analyzing: {strat_name}")
            print('=' * 60)

            strategy_report = {}

            for i, pit in enumerate(strategy.pit_stops):
                pit_key = f"pit_{i+1}"

                # Analyze sensitivity around original lap
                search_range = (max(30, pit.lap - 15), min(80, pit.lap + 15))

                sensitivity_df = self.analyze_pit_timing(
                    strategy,
                    pit_index=i,
                    lap_range=search_range,
                    lap_step=3,
                    num_sims_per_point=num_sims_per_point,
                    show_progress=False
                )

                # Find optimal
                optimal = self.find_optimal_pit_lap(
                    strategy,
                    pit_index=i,
                    search_range=search_range,
                    num_sims_per_point=num_sims_per_point
                )

                strategy_report[pit_key] = {
                    'original_lap': pit.lap,
                    'sensitivity_curve': sensitivity_df,
                    'optimal_lap': optimal['optimal_lap'],
                    'improvement': optimal['improvement'],
                    'improvement_pct': optimal['improvement_pct']
                }

            report[strat_name] = strategy_report

        return report

    def _create_modified_strategy(self,
                                  base_strategy: Strategy,
                                  pit_index: int,
                                  new_lap: int) -> Strategy:
        """Create strategy with modified pit timing"""
        new_pits = base_strategy.pit_stops.copy()
        new_pits[pit_index] = PitStop(
            lap=new_lap,
            duration=base_strategy.pit_stops[pit_index].duration,
            fuel_added=base_strategy.pit_stops[pit_index].fuel_added,
            tires_changed=base_strategy.pit_stops[pit_index].tires_changed
        )

        return Strategy(
            name=f"{base_strategy.name} (modified)",
            description=f"{base_strategy.name} with pit #{pit_index + 1} at lap {new_lap}",
            pit_stops=new_pits
        )

    def _evaluate_single_timing(self,
                                base_strategy: Strategy,
                                pit_index: int,
                                test_lap: int,
                                num_sims: int) -> float:
        """Helper to evaluate single pit timing"""
        modified_strategy = self._create_modified_strategy(
            base_strategy, pit_index, test_lap
        )

        metrics = self.mc_evaluator.evaluate_strategy(
            modified_strategy,
            num_simulations=num_sims,
            show_progress=False
        )

        return metrics['mean_position']


def create_sensitivity_plot(sensitivity_df: pd.DataFrame,
                            original_lap: int,
                            title: str = "Sensitivity Analysis") -> Dict:
    """
    Create plot data for sensitivity curve.

    Args:
        sensitivity_df: DataFrame from analyze_pit_timing
        original_lap: Original pit lap for reference
        title: Plot title

    Returns:
        Dict with plot data for visualization
    """
    plot_data = {
        'x': sensitivity_df['pit_lap'].tolist(),
        'y': sensitivity_df['mean_position'].tolist(),
        'y_upper': (sensitivity_df['mean_position'] + sensitivity_df['std_position']).tolist(),
        'y_lower': (sensitivity_df['mean_position'] - sensitivity_df['std_position']).tolist(),
        'optimal_x': sensitivity_df.loc[sensitivity_df['is_optimal'], 'pit_lap'].values[0]
        if any(sensitivity_df['is_optimal']) else None,
        'optimal_y': sensitivity_df.loc[sensitivity_df['is_optimal'], 'mean_position'].values[0]
        if any(sensitivity_df['is_optimal']) else None,
        'original_x': original_lap,
        'original_y': sensitivity_df.loc[sensitivity_df['pit_lap'] == original_lap, 'mean_position'].values[0]
        if (sensitivity_df['pit_lap'] == original_lap).any() else None,
        'title': title
    }

    return plot_data


if __name__ == '__main__':
    # Test sensitivity analysis
    import sys
    sys.path.insert(0, '.')

    from src.strategy import PRESET_STRATEGIES

    print("Testing Sensitivity Analysis")
    print("=" * 60)

    # Quick test
    sim_config = {
        'num_cars': 10,
        'num_laps': 50
    }

    evaluator = MonteCarloEvaluator(sim_config, n_jobs=2)
    analyzer = StrategySensitivityAnalyzer(evaluator)

    # Test single pit analysis
    print("\n1. Single Pit Analysis")
    print("-" * 40)
    sensitivity_df = analyzer.analyze_pit_timing(
        PRESET_STRATEGIES['standard'],
        pit_index=0,
        lap_range=(30, 60),
        lap_step=5,
        num_sims_per_point=10,
        show_progress=True
    )

    print(f"\nSensitivity Results:")
    print(sensitivity_df[['pit_lap', 'mean_position', 'std_position', 'win_rate']])

    # Test optimization
    print("\n2. Pit Optimization")
    print("-" * 40)
    result = analyzer.find_optimal_pit_lap(
        PRESET_STRATEGIES['standard'],
        pit_index=0,
        search_range=(35, 65),
        num_sims_per_point=10
    )

    print(f"\nOptimization Results:")
    print(f"  Original lap: {result['original_lap']}")
    print(f"  Optimal lap: {result['optimal_lap']}")
    print(f"  Improvement: {result['improvement']:.1f} positions")
