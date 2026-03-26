"""
Tests for NASCAR points system implementation.

Tests stage points, final points, and expected points calculations.
"""
import pytest
import numpy as np
from src.nascar_points import (
    StagePoints,
    RacePoints,
    calculate_expected_points,
    calculate_single_race_points,
    _get_stage_points,
    _get_final_points,
    points_vs_position_optimization_diff
)


class TestStagePoints:
    """Test StagePoints calculation."""

    def test_stage_points_top_10(self):
        """Test stage points for top 10 positions."""
        for position in range(1, 11):
            expected = 11 - position  # 1st=10, 2nd=9, ..., 10th=1
            stage = StagePoints(stage_number=1, position=position)
            assert stage.points_earned == expected

    def test_stage_points_beyond_10th(self):
        """Test that positions beyond 10th get 0 stage points."""
        for position in range(11, 40):
            stage = StagePoints(stage_number=1, position=position)
            assert stage.points_earned == 0


class TestRacePoints:
    """Test RacePoints calculation."""

    def test_calculate_final_points_winner(self):
        """Test that winner gets 40 points + 1 playoff point."""
        race_points = RacePoints(final_position=1)
        race_points.calculate_final_points(1)

        assert race_points.final_stage_points == 40
        assert race_points.playoff_points == 1
        assert race_points.total_points == 41

    def test_calculate_final_points_second(self):
        """Test that second place gets 35 points."""
        race_points = RacePoints(final_position=2)
        race_points.calculate_final_points(2)

        assert race_points.final_stage_points == 35
        assert race_points.playoff_points == 0
        assert race_points.total_points == 35

    def test_calculate_final_points_third(self):
        """Test that third place gets 34 points."""
        race_points = RacePoints(final_position=3)
        race_points.calculate_final_points(3)

        assert race_points.final_stage_points == 34
        assert race_points.playoff_points == 0

    def test_calculate_final_points_4th_to_36th(self):
        """Test points for positions 4-36."""
        for position in range(4, 37):
            expected = 37 - position  # 4th=33, 5th=32, ..., 36th=1
            points = _get_final_points(position)
            assert points == expected

    def test_calculate_final_points_beyond_36th(self):
        """Test that positions beyond 36th get 0 points."""
        for position in range(37, 43):
            race_points = RacePoints(final_position=position)
            race_points.calculate_final_points(position)
            assert race_points.final_stage_points == 0

    def test_calculate_stage_points_stage1(self):
        """Test calculating stage 1 points."""
        race_points = RacePoints()
        race_points.calculate_stage_points(stage_number=1, position=5)

        assert race_points.stage1_position == 5
        assert race_points.stage1_points == 6  # 5th place = 6 points

    def test_calculate_stage_points_stage2(self):
        """Test calculating stage 2 points."""
        race_points = RacePoints()
        race_points.calculate_stage_points(stage_number=2, position=3)

        assert race_points.stage2_position == 3
        assert race_points.stage2_points == 8  # 3rd place = 8 points

    def test_total_points_calculation(self):
        """Test total points calculation across all stages."""
        race_points = RacePoints()

        # Add stage points
        race_points.calculate_stage_points(1, 5)  # 6 points
        race_points.calculate_stage_points(2, 3)  # 8 points

        # Add final points
        race_points.calculate_final_points(1)  # 40 points + 1 playoff

        assert race_points.stage_points == 14  # 6 + 8
        assert race_points.final_stage_points == 40
        assert race_points.playoff_points == 1
        assert race_points.total_points == 55  # 14 + 40 + 1


class TestCalculateExpectedPoints:
    """Test expected points calculation from simulation results."""

    def test_expected_points_basic(self):
        """Test basic expected points calculation."""
        # Simple case: always finish 10th
        stage1_positions = [10] * 100
        stage2_positions = [10] * 100
        final_positions = [10] * 100

        expected = calculate_expected_points(
            stage1_positions,
            stage2_positions,
            final_positions
        )

        # 10th place: 1 stage point each stage, 27 final points
        assert expected['expected_stage1_points'] == 1.0
        assert expected['expected_stage2_points'] == 1.0
        assert expected['expected_final_points'] == 27.0
        assert expected['expected_total_points'] == 29.0

    def test_expected_points_winner(self):
        """Test expected points when always winning."""
        stage1_positions = [1] * 100
        stage2_positions = [1] * 100
        final_positions = [1] * 100

        expected = calculate_expected_points(
            stage1_positions,
            stage2_positions,
            final_positions
        )

        # Winner: 10 stage points each, 40 final, 1 playoff
        assert expected['expected_stage1_points'] == 10.0
        assert expected['expected_stage2_points'] == 10.0
        assert expected['expected_final_points'] == 40.0
        assert expected['expected_playoff_points'] == 1.0
        assert expected['expected_total_points'] == 61.0

    def test_expected_probabilities(self):
        """Test probability calculations."""
        # 50% chance of top 10, 10% chance of winning
        stage1_positions = [1] * 10 + list(range(11, 21)) * 9  # 10 wins, 90 >10th
        stage2_positions = [1] * 10 + list(range(11, 21)) * 9
        final_positions = [1] * 10 + list(range(11, 21)) * 9

        expected = calculate_expected_points(
            stage1_positions,
            stage2_positions,
            final_positions
        )

        # 10% win rate
        assert expected['probability_win_stage1'] == 0.1
        assert expected['probability_win_stage2'] == 0.1
        assert expected['probability_win_race'] == 0.1

        # 10% top-10 rate (only winners in this example)
        assert expected['probability_top10_stage1'] == 0.1
        assert expected['probability_top10_stage2'] == 0.1

    def test_expected_points_with_none_values(self):
        """Test that None values are filtered out."""
        stage1_positions = [1, 2, 3, None, None]
        stage2_positions = [1, 2, None, 4, None]
        final_positions = [1, 2, 3, 4, 5]

        expected = calculate_expected_points(
            stage1_positions,
            stage2_positions,
            final_positions
        )

        # Should only count non-None values
        assert expected['expected_stage1_points'] == pytest.approx((10 + 9 + 8) / 3)
        assert expected['expected_stage2_points'] == pytest.approx((10 + 9 + 7) / 3)


class TestCalculateSingleRacePoints:
    """Test single race points calculation."""

    def test_single_race_all_stages(self):
        """Test calculating points for a complete race."""
        race_points = calculate_single_race_points(
            stage1_position=5,
            stage2_position=3,
            final_position=1
        )

        assert race_points.stage1_points == 6
        assert race_points.stage2_points == 8
        assert race_points.final_stage_points == 40
        assert race_points.playoff_points == 1
        assert race_points.total_points == 55

    def test_single_race_no_stage1(self):
        """Test calculating points when stage 1 position is missing."""
        race_points = calculate_single_race_points(
            stage1_position=None,
            stage2_position=5,
            final_position=10
        )

        assert race_points.stage1_points == 0
        assert race_points.stage2_points == 6
        assert race_points.final_stage_points == 27
        assert race_points.total_points == 33


class TestPointsVsPositionOptimization:
    """Test comparing points vs position optimization."""

    def test_points_better(self):
        """Test when points-optimized strategy is better."""
        points_metrics = {
            'mean_position': 12.0,
            'expected_total_points': 35.0,
            'win_rate': 0.10,
            'top10_rate': 0.50
        }

        position_metrics = {
            'mean_position': 11.0,
            'expected_total_points': 30.0,
            'win_rate': 0.08,
            'top10_rate': 0.45
        }

        diff = points_vs_position_optimization_diff(points_metrics, position_metrics)

        # Points strategy gives 5 more points but 1 worse position
        assert diff['expected_points_diff'] == 5.0
        # Negative means points_metrics has worse (higher) position
        assert diff['mean_position_diff'] == -1.0  # 11 - 12 = -1 (points is worse)
        assert diff['better_for'] == 'points'  # Points strategy earns more points

    def test_position_better(self):
        """Test when position-optimized strategy is better."""
        points_metrics = {
            'mean_position': 15.0,
            'expected_total_points': 28.0,
            'win_rate': 0.05,
            'top10_rate': 0.30
        }

        position_metrics = {
            'mean_position': 10.0,
            'expected_total_points': 32.0,
            'win_rate': 0.12,
            'top10_rate': 0.60
        }

        diff = points_vs_position_optimization_diff(points_metrics, position_metrics)

        # Position strategy is better at both
        assert diff['expected_points_diff'] == -4.0  # position has more points
        # Negative means position_metrics has better (lower) position
        assert diff['mean_position_diff'] == -5.0  # 10 - 15 = -5
        # 'better_for' refers to who has more points, not better position
        assert diff['better_for'] == 'position'  # Position strategy earns more points


class TestNASCARPointsIntegration:
    """Integration tests for NASCAR points with simulation."""

    def test_points_calculation_from_simulations(self):
        """Test calculating expected points from simulation results."""
        # Simulate 100 races with varying results
        np.random.seed(42)
        n_sims = 100

        stage1_positions = np.random.randint(1, 40, n_sims).tolist()
        stage2_positions = np.random.randint(1, 40, n_sims).tolist()
        final_positions = np.random.randint(1, 40, n_sims).tolist()

        expected = calculate_expected_points(
            stage1_positions,
            stage2_positions,
            final_positions
        )

        # Check that expected values are reasonable
        assert 0 <= expected['expected_stage1_points'] <= 10
        assert 0 <= expected['expected_stage2_points'] <= 10
        assert 0 <= expected['expected_final_points'] <= 40
        assert 0 <= expected['expected_total_points'] <= 61

        # Check probabilities are valid
        assert 0 <= expected['probability_win_stage1'] <= 1
        assert 0 <= expected['probability_win_stage2'] <= 1
        assert 0 <= expected['probability_win_race'] <= 1

    def test_points_stage_final_correlation(self):
        """Test correlation between stage and final positions."""
        # Good stage positions should correlate with good final positions
        np.random.seed(42)
        n_sims = 100

        # Cars that run well in stages tend to run well overall
        stage1_positions = np.random.randint(1, 20, n_sims).tolist()
        stage2_positions = np.random.randint(1, 20, n_sims).tolist()
        final_positions = np.random.randint(1, 25, n_sims).tolist()

        expected = calculate_expected_points(
            stage1_positions,
            stage2_positions,
            final_positions
        )

        # Should earn more points than average
        assert expected['expected_total_points'] > 20
