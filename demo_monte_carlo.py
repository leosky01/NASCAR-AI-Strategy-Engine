"""
Demo script for Monte Carlo strategy evaluation.

Shows how to use the Monte Carlo engine to compare strategies.
"""
import pandas as pd
from src.monte_carlo import MonteCarloEvaluator, calculate_statistical_significance
from src.strategy import PRESET_STRATEGIES

print("=" * 70)
print("NASCAR Monte Carlo Strategy Evaluation - Demo")
print("=" * 70)

# Configuration
SIM_CONFIG = {
    'num_cars': 40,
    'num_laps': 100  # Shorter for faster demo
}
NUM_SIMULATIONS = 50  # Adjust based on time

print(f"\n⚙️  Configuration:")
print(f"  Cars: {SIM_CONFIG['num_cars']}")
print(f"  Laps: {SIM_CONFIG['num_laps']}")
print(f"  Simulations per strategy: {NUM_SIMULATIONS}")

# Create evaluator
evaluator = MonteCarloEvaluator(SIM_CONFIG, n_jobs=-1)

# Select strategies to compare
print(f"\n📋 Comparing strategies:")
for name in PRESET_STRATEGIES.keys():
    print(f"  - {name}")

# Run comparison
print(f"\n🏃 Running Monte Carlo simulations...")
comparison, results = evaluator.compare_strategies(
    PRESET_STRATEGIES,
    num_simulations=NUM_SIMULATIONS,
    show_progress=True
)

# Display results
print(f"\n" + "=" * 70)
print("STRATEGY COMPARISON RESULTS")
print("=" * 70)
print(comparison)

# Find best strategy
print(f"\n" + "=" * 70)
print("BEST STRATEGY ANALYSIS")
print("=" * 70)

best_name, best_metrics = evaluator.find_best_strategy(
    PRESET_STRATEGIES,
    metric='mean_position',
    num_simulations=NUM_SIMULATIONS
)

print(f"\n🏆 Best Strategy (by average position): {best_name}")
print(f"   Mean Position: {best_metrics['mean_position']:.2f}")
print(f"   Win Rate: {best_metrics['win_rate']:.1%}")
print(f"   Top-10 Rate: {best_metrics['top10_rate']:.1%}")
print(f"   Std Dev: {best_metrics['std_position']:.2f}")

# Statistical significance
print(f"\n" + "=" * 70)
print("STATISTICAL SIGNIFICANCE TESTS")
print("=" * 70)

# Compare best vs worst
strategies_list = list(results.keys())
if len(strategies_list) >= 2:
    # Find by mean position
    sorted_strategies = sorted(strategies_list, key=lambda k: results[k]['mean_position'])
    worst = sorted_strategies[-1]
    best = sorted_strategies[0]

    print(f"\nComparing: {best} vs {worst}")
    stats = calculate_statistical_significance(results[best], results[worst])

    print(f"  Mean difference: {stats['mean_difference']:.2f} positions")
    print(f"  P-value: {stats['p_value']:.4f}")
    print(f"  Significant: {'Yes' if stats['significant'] else 'No'}")
    print(f"  Winner: {stats['winner']}")
    print(f"  Effect size (Cohen's d): {stats['cohens_d']:.2f}")

print(f"\n" + "=" * 70)
print("✅ Demo Complete!")
print("=" * 70)
