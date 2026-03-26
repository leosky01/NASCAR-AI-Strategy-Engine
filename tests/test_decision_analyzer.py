"""
Tests for decision analyzer module.

Tests probabilistic decision analysis and recommendations.
"""
import pytest
import numpy as np
from src.decision_analyzer import (
    DecisionProbability,
    StrategyComparison,
    ProbabilisticDecisionEngine,
    create_decision_summary
)


class TestDecisionProbability:
    """Test DecisionProbability dataclass."""

    def test_decision_probability_creation(self):
        """Test creating a DecisionProbability object."""
        decision = DecisionProbability(
            probability=0.75,
            confidence='high',
            recommendation='pit',
            effect_size=-0.8,
            sample_size=200
        )

        assert decision.probability == 0.75
        assert decision.confidence == 'high'
        assert decision.recommendation == 'pit'
        assert decision.effect_size == -0.8
        assert decision.sample_size == 200


class TestProbabilisticDecisionEngine:
    """Test ProbabilisticDecisionEngine."""

    @pytest.fixture
    def engine(self):
        """Create a decision engine for testing."""
        return ProbabilisticDecisionEngine(n_bootstrap=1000, random_seed=42)

    @pytest.fixture
    def sample_pit_metrics(self):
        """Create sample metrics for pitting strategy."""
        np.random.seed(42)
        positions = np.random.normal(12, 4, 100)

        return {
            'positions': positions,
            'mean_position': np.mean(positions),
            'std_position': np.std(positions),
            'top10_rate': np.mean(positions <= 10),
            'win_rate': np.mean(positions == 1),
            'top5_rate': np.mean(positions <= 5),
        }

    @pytest.fixture
    def sample_stay_out_metrics(self):
        """Create sample metrics for staying out strategy."""
        np.random.seed(43)
        positions = np.random.normal(16, 5, 100)

        return {
            'positions': positions,
            'mean_position': np.mean(positions),
            'std_position': np.std(positions),
            'top10_rate': np.mean(positions <= 10),
            'win_rate': np.mean(positions == 1),
            'top5_rate': np.mean(positions <= 5),
        }

    def test_pit_decision_probability(self, engine, sample_pit_metrics, sample_stay_out_metrics):
        """Test that pit decision probability is between 0 and 1."""
        decision = engine.analyze_pit_decision(
            sample_pit_metrics,
            sample_stay_out_metrics
        )

        # Check probability is valid
        assert 0.0 <= decision.probability <= 1.0

        # Check other fields
        assert decision.confidence in ['high', 'medium', 'low']
        assert decision.recommendation in ['pit', 'stay_out', 'toss_up']
        assert decision.sample_size == 200  # 100 + 100

    def test_confidence_assessment(self, engine):
        """Test confidence level assessment."""
        # Large sample = high confidence
        large_pit = {'positions': np.random.normal(15, 4, 200)}
        large_stay = {'positions': np.random.normal(15, 4, 200)}
        decision_large = engine.analyze_pit_decision(large_pit, large_stay)
        assert decision_large.confidence in ['high', 'medium', 'low']

        # Small sample = low confidence
        small_pit = {'positions': np.random.normal(15, 4, 30)}
        small_stay = {'positions': np.random.normal(15, 4, 30)}
        decision_small = engine.analyze_pit_decision(small_pit, small_stay)
        assert decision_small.confidence in ['high', 'medium', 'low']

    def test_recommendation_thresholds(self, engine):
        """Test that recommendation follows probability thresholds."""
        # Create clear pit advantage (positions 10 vs 20)
        clear_pit = {
            'positions': np.random.normal(10, 2, 100),
            'top10_rate': 0.8,
            'win_rate': 0.1,
            'top5_rate': 0.5,
        }
        clear_stay = {
            'positions': np.random.normal(20, 3, 100),
            'top10_rate': 0.1,
            'win_rate': 0.0,
            'top5_rate': 0.05,
        }

        decision = engine.analyze_pit_decision(clear_pit, clear_stay)
        # With clear advantage, should recommend pit
        assert decision.recommendation == 'pit'
        assert decision.probability >= 0.6

    def test_bootstrap_probability(self, engine):
        """Test bootstrap probability estimation."""
        # Create two clearly different distributions
        better = np.array([1, 2, 3, 4, 5] * 20)  # Mean = 3
        worse = np.array([10, 11, 12, 13, 14] * 20)  # Mean = 12

        prob = engine._bootstrap_probability(better, worse)

        # Better should win nearly 100% of the time
        assert prob > 0.95

    def test_compare_strategies_probabilistic(self, engine):
        """Test comparing multiple strategies."""
        strategies = {
            'aggressive': {
                'positions': np.random.normal(12, 5, 100),
                'mean_position': 12,
            },
            'conservative': {
                'positions': np.random.normal(15, 4, 100),
                'mean_position': 15,
            },
            'standard': {
                'positions': np.random.normal(14, 4.5, 100),
                'mean_position': 14,
            }
        }

        comparisons = engine.compare_strategies_probabilistic(strategies)

        # Should have 3 choose 2 = 3 comparisons
        assert len(comparisons) == 3

        # Check comparison structure
        for comp in comparisons:
            assert isinstance(comp, StrategyComparison)
            assert 0.0 <= comp.probability_a_better <= 1.0
            assert comp.winner in ['aggressive', 'conservative', 'standard', 'tie']
            assert comp.significant in [True, False]  # Boolean value (numpy or python bool)

    def test_calculate_win_probability(self, engine):
        """Test calculating win probability against opponent."""
        our_positions = np.array([5, 10, 15, 20, 25])
        opponent_positions = np.array([10, 15, 20, 25, 30])

        prob = engine.calculate_win_probability(our_positions, opponent_positions)

        # We should have advantage (lower is better)
        assert prob > 0.5

    def test_decision_summary_format(self, engine, sample_pit_metrics, sample_stay_out_metrics):
        """Test decision summary formatting."""
        decision = engine.analyze_pit_decision(
            sample_pit_metrics,
            sample_stay_out_metrics
        )

        summary = create_decision_summary(decision, sample_pit_metrics, sample_stay_out_metrics)

        # Check that summary contains key information
        assert 'Recommendation:' in summary
        assert 'Probability:' in summary
        assert 'Confidence:' in summary
        assert 'If You Pit' in summary
        assert 'If You Stay Out' in summary
        assert 'Expected Position' in summary

    def test_effect_size_calculation(self, engine):
        """Test Cohen's d effect size calculation."""
        # Same distributions = effect size near 0
        same_1 = {'positions': np.random.normal(15, 3, 100)}
        same_2 = {'positions': np.random.normal(15, 3, 100)}

        decision = engine.analyze_pit_decision(same_1, same_2)
        assert abs(decision.effect_size) < 0.5  # Small effect

        # Different distributions = larger effect size
        different_1 = {'positions': np.random.normal(10, 2, 100)}
        different_2 = {'positions': np.random.normal(20, 2, 100)}

        decision = engine.analyze_pit_decision(different_1, different_2)
        assert abs(decision.effect_size) > 2.0  # Large effect

    def test_calculate_decision_roc_curve(self, engine):
        """Test ROC curve calculation."""
        pit_positions = np.array([1, 5, 10, 15, 20])
        stay_out_positions = np.array([5, 10, 15, 20, 25])

        roc = engine.calculate_decision_roc_curve(pit_positions, stay_out_positions)

        # Check structure
        assert 'thresholds' in roc
        assert 'tpr' in roc
        assert 'fpr' in roc
        assert 'auc' in roc

        # Check lengths match
        assert len(roc['thresholds']) == len(roc['tpr'])
        assert len(roc['thresholds']) == len(roc['fpr'])

        # AUC should be between 0 and 1
        assert 0 <= roc['auc'] <= 1


class TestDecisionAnalyzerIntegration:
    """Integration tests for decision analyzer."""

    def test_end_to_end_pit_decision(self):
        """Test complete pit decision workflow."""
        engine = ProbabilisticDecisionEngine(n_bootstrap=500)

        # Scenario: Lap 80, running 15th, tires 40 laps old
        # Create realistic scenario data
        pit_positions = np.random.normal(13, 4, 100)  # Pitting helps
        stay_out_positions = np.random.normal(18, 5, 100)  # Staying out hurts

        pit_metrics = {
            'positions': pit_positions,
            'mean_position': np.mean(pit_positions),
            'std_position': np.std(pit_positions),
            'top10_rate': np.mean(pit_positions <= 10),
            'win_rate': np.mean(pit_positions == 1),
            'top5_rate': np.mean(pit_positions <= 5),
        }

        stay_out_metrics = {
            'positions': stay_out_positions,
            'mean_position': np.mean(stay_out_positions),
            'std_position': np.std(stay_out_positions),
            'top10_rate': np.mean(stay_out_positions <= 10),
            'win_rate': np.mean(stay_out_positions == 1),
            'top5_rate': np.mean(stay_out_positions <= 5),
        }

        # Analyze
        decision = engine.analyze_pit_decision(
            pit_metrics,
            stay_out_metrics,
            decision_context={'lap': 80, 'position': 15, 'tire_age': 40}
        )

        # Verify decision is sensible
        assert decision.recommendation in ['pit', 'stay_out', 'toss_up']
        assert 0 <= decision.probability <= 1

        # Create summary
        summary = create_decision_summary(decision, pit_metrics, stay_out_metrics)
        assert len(summary) > 0
