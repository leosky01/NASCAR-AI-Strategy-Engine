"""
Probabilistic decision analyzer for NASCAR strategy.

Converts Monte Carlo simulation results into probability distributions
and actionable recommendations for race strategy decisions.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats


@dataclass
class DecisionProbability:
    """
    Probability distribution for a binary decision.

    Represents the likelihood that one option is better than another.
    """
    probability: float  # 0.0-1.0 (e.g., 0.75 = 75% pit is better)
    confidence: str  # 'high', 'medium', 'low'
    recommendation: str  # 'pit', 'stay_out', 'toss_up'
    effect_size: float  # Cohen's d
    sample_size: int  # Number of simulations

    def __str__(self):
        pct = self.probability * 100
        return (f"{self.recommendation.upper()} - {pct:.1f}% probability\n"
                f"Confidence: {self.confidence.upper()} ({self.sample_size} simulations)")


@dataclass
class StrategyComparison:
    """
    Pairwise comparison of two strategies with statistical analysis.
    """
    strategy_a_name: str
    strategy_b_name: str
    probability_a_better: float  # P(A < B) for positions (lower is better)
    mean_difference: float
    cohens_d: float
    p_value: float
    significant: bool
    winner: str  # 'A' or 'B' or 'tie'

    def __str__(self):
        pct_better = self.probability_a_better * 100
        return (f"P({self.strategy_a_name} better) = {pct_better:.1f}%\n"
                f"Winner: {self.winner} (Cohen's d: {self.cohens_d:.2f})")


class ProbabilisticDecisionEngine:
    """
    Converts Monte Carlo results into probabilistic decisions.

    Uses bootstrap resampling and statistical tests to estimate
    the probability that one strategy is better than another.
    """

    def __init__(self, n_bootstrap: int = 1000, random_seed: Optional[int] = None):
        """
        Initialize decision engine.

        Args:
            n_bootstrap: Number of bootstrap iterations for probability estimation
            random_seed: For reproducibility
        """
        self.n_bootstrap = n_bootstrap
        self.rng = np.random.RandomState(random_seed)

    def analyze_pit_decision(self,
                            pit_metrics: Dict,
                            stay_out_metrics: Dict,
                            decision_context: Optional[Dict] = None) -> DecisionProbability:
        """
        Analyze whether to pit or stay out.

        Returns a probability distribution and recommendation.

        Args:
            pit_metrics: Monte Carlo metrics if pitting
            stay_out_metrics: Monte Carlo metrics if staying out
            decision_context: Optional context (lap, position, tire_age, etc.)

        Returns:
            DecisionProbability with recommendation
        """
        # Extract positions (lower is better)
        pit_positions = np.array(pit_metrics['positions'])
        stay_out_positions = np.array(stay_out_metrics['positions'])

        # Bootstrap to estimate P(pit < stay_out)
        # For positions, lower is better, so we want P(pit_position < stay_out_position)
        prob_pit_better = self._bootstrap_probability(
            pit_positions, stay_out_positions
        )

        # Calculate effect size (Cohen's d)
        # Negative means pit is better (lower positions)
        pooled_std = np.sqrt(
            (np.std(pit_positions)**2 + np.std(stay_out_positions)**2) / 2
        )
        cohens_d = (np.mean(pit_positions) - np.mean(stay_out_positions)) / pooled_std

        # Assess confidence
        confidence = self._assess_confidence(
            len(pit_positions) + len(stay_out_positions),
            abs(cohens_d)
        )

        # Make recommendation
        # Note: prob_pit_better is P(pit_position < stay_out_position)
        # If prob_pit_better >= 0.6, pit is better (lower positions)
        # If prob_pit_better <= 0.4, stay out is better
        if prob_pit_better >= 0.60:
            recommendation = 'pit'
        elif prob_pit_better <= 0.40:
            recommendation = 'stay_out'
        else:
            recommendation = 'toss_up'

        return DecisionProbability(
            probability=prob_pit_better,
            confidence=confidence,
            recommendation=recommendation,
            effect_size=cohens_d,
            sample_size=len(pit_positions) + len(stay_out_positions)
        )

    def compare_strategies_probabilistic(self,
                                       strategies: Dict[str, Dict],
                                       metric: str = 'mean_position') -> List[StrategyComparison]:
        """
        Compare multiple strategies pairwise with probability analysis.

        Args:
            strategies: Dict mapping strategy name to metrics dict
            metric: Metric to compare ('mean_position', 'win_rate', etc.)

        Returns:
            List of StrategyComparison objects for all pairwise comparisons
        """
        comparisons = []
        strategy_names = list(strategies.keys())

        for i in range(len(strategy_names)):
            for j in range(i + 1, len(strategy_names)):
                name_a = strategy_names[i]
                name_b = strategy_names[j]

                metrics_a = strategies[name_a]
                metrics_b = strategies[name_b]

                # Extract positions
                positions_a = np.array(metrics_a['positions'])
                positions_b = np.array(metrics_b['positions'])

                # Bootstrap probability
                prob_a_better = self._bootstrap_probability(positions_a, positions_b)

                # Statistical tests
                mean_diff = np.mean(positions_a) - np.mean(positions_b)

                # T-test
                t_stat, p_value = stats.ttest_ind(positions_a, positions_b)

                # Cohen's d
                pooled_std = np.sqrt(
                    (np.std(positions_a)**2 + np.std(positions_b)**2) / 2
                )
                cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

                # Determine winner (lower position is better)
                if mean_diff < 0:
                    winner = name_a
                elif mean_diff > 0:
                    winner = name_b
                else:
                    winner = 'tie'

                # Check significance
                significant = p_value < 0.05

                comparisons.append(StrategyComparison(
                    strategy_a_name=name_a,
                    strategy_b_name=name_b,
                    probability_a_better=prob_a_better,
                    mean_difference=mean_diff,
                    cohens_d=cohens_d,
                    p_value=p_value,
                    significant=significant,
                    winner=winner
                ))

        return comparisons

    def calculate_win_probability(self,
                                 our_positions: np.ndarray,
                                 opponent_positions: np.ndarray) -> float:
        """
        Calculate probability of beating an opponent.

        Args:
            our_positions: Our finishing positions from simulations
            opponent_positions: Opponent's finishing positions

        Returns:
            Probability (0-1) that we finish ahead of opponent
        """
        # Bootstrap estimate of P(our_position < opponent_position)
        return self._bootstrap_probability(our_positions, opponent_positions)

    def _bootstrap_probability(self,
                              sample_a: np.ndarray,
                              sample_b: np.ndarray) -> float:
        """
        Use bootstrap resampling to estimate P(A < B).

        For positions, lower is better.

        Args:
            sample_a: First sample (e.g., pit positions)
            sample_b: Second sample (e.g., stay out positions)

        Returns:
            Estimated probability that A < B
        """
        n_bootstrap = self.n_bootstrap

        # Resample with replacement
        boot_means_a = [
            np.mean(self.rng.choice(sample_a, size=len(sample_a), replace=True))
            for _ in range(n_bootstrap)
        ]
        boot_means_b = [
            np.mean(self.rng.choice(sample_b, size=len(sample_b), replace=True))
            for _ in range(n_bootstrap)
        ]

        # Count how often A's mean is less than B's mean
        prob_a_better = np.mean([a < b for a, b in zip(boot_means_a, boot_means_b)])

        return prob_a_better

    def _assess_confidence(self, sample_size: int, effect_size: float) -> str:
        """
        Assess confidence level based on sample size and effect size.

        Args:
            sample_size: Total number of simulations
            effect_size: Absolute Cohen's d

        Returns:
            'high', 'medium', or 'low'
        """
        # High confidence: large sample OR large effect
        if sample_size >= 200 or (sample_size >= 100 and effect_size >= 0.8):
            return 'high'
        # Medium confidence: moderate sample and effect
        elif sample_size >= 100 or (sample_size >= 50 and effect_size >= 0.5):
            return 'medium'
        # Low confidence: small sample and small effect
        else:
            return 'low'

    def calculate_decision_roc_curve(self,
                                    pit_positions: np.ndarray,
                                    stay_out_positions: np.ndarray) -> Dict:
        """
        Calculate ROC curve for pit decision at different position thresholds.

        Args:
            pit_positions: Finishing positions when pitting
            stay_out_positions: Finishing positions when staying out

        Returns:
            Dict with ROC curve data (sensitivity, specificity, thresholds)
        """
        thresholds = range(1, 43)  # Position 1 to 42

        tpr_list = []  # True positive rate (sensitivity)
        fpr_list = []  # False positive rate

        for threshold in thresholds:
            # At this threshold, we recommend pit if expected position <= threshold
            pit_better = np.mean(pit_positions <= threshold)
            stay_out_better = np.mean(stay_out_positions <= threshold)

            # True positive: pit is actually better
            tpr_list.append(pit_better)
            # False positive: stay out would have been better
            fpr_list.append(stay_out_better)

        return {
            'thresholds': list(thresholds),
            'tpr': tpr_list,
            'fpr': fpr_list,
            'auc': np.trapz(tpr_list, fpr_list)  # Area under curve
        }


def create_decision_summary(decision: DecisionProbability,
                           pit_metrics: Dict,
                           stay_out_metrics: Dict) -> str:
    """
    Create human-readable decision summary.

    Args:
        decision: DecisionProbability from analyze_pit_decision
        pit_metrics: Metrics for pitting strategy
        stay_out_metrics: Metrics for staying out

    Returns:
        Formatted string with decision analysis
    """
    lines = [
        f"Recommendation: {decision.recommendation.upper()}",
        f"Probability: {decision.probability * 100:.1f}%",
        f"Confidence: {decision.confidence.upper()} ({decision.sample_size} simulations)",
        "",
        "If You Pit              If You Stay Out",
        "─────────────────       ─────────────────"
    ]

    # Add comparison metrics
    metrics_to_compare = [
        ('Expected Position', 'mean_position', '{:.1f} pos'),
        ('Top-10', 'top10_rate', '{:.1%}'),
        ('Win', 'win_rate', '{:.1%}'),
        ('Top-5', 'top5_rate', '{:.1%}'),
    ]

    for label, key, fmt in metrics_to_compare:
        pit_val = pit_metrics[key]
        stay_val = stay_out_metrics[key]
        lines.append(f"{label:12} {fmt.format(pit_val):>15}       {fmt.format(stay_val):>15}")

    return "\n".join(lines)


if __name__ == '__main__':
    # Test decision analyzer
    print("Testing Decision Analyzer")
    print("=" * 60)

    # Create synthetic data
    np.random.seed(42)

    # Scenario 1: Clear choice to pit
    print("\nScenario 1: Clear advantage to pit")
    pit_positions = np.random.normal(12, 5, 200)  # Better average
    stay_out_positions = np.random.normal(18, 6, 200)  # Worse average

    pit_metrics = {
        'positions': pit_positions,
        'mean_position': np.mean(pit_positions),
        'top10_rate': np.mean(pit_positions <= 10),
        'win_rate': np.mean(pit_positions == 1),
        'top5_rate': np.mean(pit_positions <= 5),
    }

    stay_out_metrics = {
        'positions': stay_out_positions,
        'mean_position': np.mean(stay_out_positions),
        'top10_rate': np.mean(stay_out_positions <= 10),
        'win_rate': np.mean(stay_out_positions == 1),
        'top5_rate': np.mean(stay_out_positions <= 5),
    }

    engine = ProbabilisticDecisionEngine(n_bootstrap=1000)
    decision = engine.analyze_pit_decision(pit_metrics, stay_out_metrics)

    print(create_decision_summary(decision, pit_metrics, stay_out_metrics))

    # Scenario 2: Toss up
    print("\n\nScenario 2: Toss up (similar outcomes)")
    pit_positions_2 = np.random.normal(15, 5, 100)
    stay_out_positions_2 = np.random.normal(15.5, 5, 100)

    pit_metrics_2 = {
        'positions': pit_positions_2,
        'mean_position': np.mean(pit_positions_2),
        'top10_rate': np.mean(pit_positions_2 <= 10),
        'win_rate': np.mean(pit_positions_2 == 1),
        'top5_rate': np.mean(pit_positions_2 <= 5),
    }

    stay_out_metrics_2 = {
        'positions': stay_out_positions_2,
        'mean_position': np.mean(stay_out_positions_2),
        'top10_rate': np.mean(stay_out_positions_2 <= 10),
        'win_rate': np.mean(stay_out_positions_2 == 1),
        'top5_rate': np.mean(stay_out_positions_2 <= 5),
    }

    decision_2 = engine.analyze_pit_decision(pit_metrics_2, stay_out_metrics_2)
    print(create_decision_summary(decision_2, pit_metrics_2, stay_out_metrics_2))
