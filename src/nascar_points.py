"""
NASCAR points system implementation.

Implements the current NASCAR stage racing points system:
- Stage points: Top 10 get points (1st=10, 2nd=9, ..., 10th=1)
- Final stage points: 1st=40, 2nd=35, 3rd=34, ..., 36th=1
- Playoff points: 1 per win
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np


@dataclass
class StagePoints:
    """Points earned in a single stage."""
    stage_number: int
    position: int
    points_earned: int = 0  # Will be calculated in __post_init__

    def __post_init__(self):
        """Calculate stage points based on position."""
        if self.position <= 10:
            # Top 10: 1st=10, 2nd=9, ..., 10th=1
            self.points_earned = 11 - self.position
        else:
            # 11th and beyond: 0 points
            self.points_earned = 0


@dataclass
class RacePoints:
    """
    Total points earned in a race.

    Includes points from all stages and final stage.
    """
    stage1_position: Optional[int] = None
    stage2_position: Optional[int] = None
    final_position: int = 40  # Default to last place

    # Points breakdown
    stage1_points: int = 0
    stage2_points: int = 0
    final_stage_points: int = 0
    playoff_points: int = 0  # 1 point per win

    @property
    def stage_points(self) -> int:
        """Total stage points (stage 1 + stage 2)."""
        return self.stage1_points + self.stage2_points

    @property
    def total_points(self) -> int:
        """Total race points (stage + final + playoff)."""
        return (self.stage1_points + self.stage2_points +
                self.final_stage_points + self.playoff_points)

    def calculate_final_points(self, position: int):
        """
        Calculate final stage points based on finishing position.

        NASCAR points system:
        - 1st: 40 points
        - 2nd: 35 points
        - 3rd: 34 points
        - 4th: 33 points
        - ...
        - 36th: 1 point
        - 37th and beyond: 0 points

        Args:
            position: Finishing position (1-40+)
        """
        self.final_position = position

        if position == 1:
            self.final_stage_points = 40
        elif position == 2:
            self.final_stage_points = 35
        elif position == 3:
            self.final_stage_points = 34
        elif 4 <= position <= 36:
            self.final_stage_points = 37 - position  # 4th=33, 5th=32, ..., 36th=1
        else:
            self.final_stage_points = 0

        # Add playoff point for winning
        if position == 1:
            self.playoff_points = 1
        else:
            self.playoff_points = 0

    def calculate_stage_points(self, stage_number: int, position: int):
        """
        Calculate points for a single stage.

        Args:
            stage_number: Stage number (1 or 2)
            position: Position at stage end
        """
        stage = StagePoints(stage_number=stage_number, position=position)

        if stage_number == 1:
            self.stage1_position = position
            self.stage1_points = stage.points_earned
        elif stage_number == 2:
            self.stage2_position = position
            self.stage2_points = stage.points_earned


def calculate_expected_points(stage1_positions: List[int],
                             stage2_positions: List[int],
                             final_positions: List[int]) -> Dict:
    """
    Calculate expected points from simulation results.

    Args:
        stage1_positions: List of positions at stage 1 end
        stage2_positions: List of positions at stage 2 end
        final_positions: List of final finishing positions

    Returns:
        Dict with expected points and probabilities
    """
    # Filter out None values
    stage1_valid = [p for p in stage1_positions if p is not None]
    stage2_valid = [p for p in stage2_positions if p is not None]
    final_valid = [p for p in final_positions if p is not None]

    # Calculate stage points
    stage1_points = [_get_stage_points(p) for p in stage1_valid]
    stage2_points = [_get_stage_points(p) for p in stage2_valid]
    final_points = [_get_final_points(p) for p in final_valid]

    # Playoff points (1 per win)
    playoff_points = [1 if p == 1 else 0 for p in final_valid]

    # Expected values
    expected_stage1_points = np.mean(stage1_points) if stage1_points else 0
    expected_stage2_points = np.mean(stage2_points) if stage2_points else 0
    expected_final_points = np.mean(final_points) if final_points else 0
    expected_playoff_points = np.mean(playoff_points) if playoff_points else 0

    expected_total_points = (
        expected_stage1_points +
        expected_stage2_points +
        expected_final_points +
        expected_playoff_points
    )

    # Probabilities
    probability_top10_stage1 = np.mean([p <= 10 for p in stage1_valid]) if stage1_valid else 0
    probability_top10_stage2 = np.mean([p <= 10 for p in stage2_valid]) if stage2_valid else 0
    probability_win_stage1 = np.mean([p == 1 for p in stage1_valid]) if stage1_valid else 0
    probability_win_stage2 = np.mean([p == 1 for p in stage2_valid]) if stage2_valid else 0
    probability_win_race = np.mean([p == 1 for p in final_valid]) if final_valid else 0

    # Stage winner probabilities
    probability_top5_stage1 = np.mean([p <= 5 for p in stage1_valid]) if stage1_valid else 0
    probability_top5_stage2 = np.mean([p <= 5 for p in stage2_valid]) if stage2_valid else 0

    return {
        'expected_stage1_points': expected_stage1_points,
        'expected_stage2_points': expected_stage2_points,
        'expected_final_points': expected_final_points,
        'expected_playoff_points': expected_playoff_points,
        'expected_total_points': expected_total_points,
        'probability_top10_stage1': probability_top10_stage1,
        'probability_top10_stage2': probability_top10_stage2,
        'probability_top5_stage1': probability_top5_stage1,
        'probability_top5_stage2': probability_top5_stage2,
        'probability_win_stage1': probability_win_stage1,
        'probability_win_stage2': probability_win_stage2,
        'probability_win_race': probability_win_race,
    }


def _get_stage_points(position: int) -> int:
    """Get stage points for a position."""
    if position <= 10:
        return 11 - position  # 1st=10, 2nd=9, ..., 10th=1
    return 0


def _get_final_points(position: int) -> int:
    """Get final stage points for a position."""
    if position == 1:
        return 40
    elif position == 2:
        return 35
    elif position == 3:
        return 34
    elif 4 <= position <= 36:
        return 37 - position
    return 0


def calculate_single_race_points(stage1_position: Optional[int],
                                 stage2_position: Optional[int],
                                 final_position: int) -> RacePoints:
    """
    Calculate points for a single race outcome.

    Args:
        stage1_position: Position at stage 1 end (None if not applicable)
        stage2_position: Position at stage 2 end (None if not applicable)
        final_position: Final finishing position

    Returns:
        RacePoints object with calculated points
    """
    race_points = RacePoints(
        stage1_position=stage1_position,
        stage2_position=stage2_position,
        final_position=final_position
    )

    # Calculate stage 1 points
    if stage1_position is not None:
        race_points.calculate_stage_points(1, stage1_position)

    # Calculate stage 2 points
    if stage2_position is not None:
        race_points.calculate_stage_points(2, stage2_position)

    # Calculate final points
    race_points.calculate_final_points(final_position)

    return race_points


def points_vs_position_optimization_diff(points_metrics: Dict,
                                        position_metrics: Dict) -> Dict:
    """
    Compare points-optimized vs position-optimized strategies.

    Args:
        points_metrics: Metrics from points-based optimization
        position_metrics: Metrics from position-based optimization

    Returns:
        Dict with differences and insights
    """
    points_diff = {
        'mean_position_diff': (
            position_metrics['mean_position'] - points_metrics['mean_position']
        ),
        'expected_points_diff': (
            points_metrics['expected_total_points'] - position_metrics['expected_total_points']
        ),
        'win_rate_diff': (
            points_metrics['win_rate'] - position_metrics['win_rate']
        ),
        'top10_rate_diff': (
            points_metrics['top10_rate'] - position_metrics['top10_rate']
        ),
    }

    # Interpretation
    if points_diff['expected_points_diff'] > 0:
        points_diff['better_for'] = 'points'
    elif points_diff['expected_points_diff'] < 0:
        points_diff['better_for'] = 'position'
    else:
        points_diff['better_for'] = 'tie'

    return points_diff


if __name__ == '__main__':
    # Test NASCAR points calculation
    print("Testing NASCAR Points System")
    print("=" * 60)

    # Test single race
    print("\nTest 1: Single Race Calculation")
    print("-" * 40)

    race_points = calculate_single_race_points(
        stage1_position=5,
        stage2_position=3,
        final_position=1
    )

    print(f"Stage 1: Position {race_points.stage1_position} = {race_points.stage1_points} pts")
    print(f"Stage 2: Position {race_points.stage2_position} = {race_points.stage2_points} pts")
    print(f"Final: Position {race_points.final_position} = {race_points.final_stage_points} pts")
    print(f"Playoff Points: {race_points.playoff_points}")
    print(f"Total: {race_points.total_points} pts")

    # Test expected points from simulations
    print("\n\nTest 2: Expected Points from Simulations")
    print("-" * 40)

    np.random.seed(42)
    n_sims = 1000

    # Generate synthetic positions
    stage1_positions = np.random.randint(1, 40, n_sims)
    stage2_positions = np.random.randint(1, 40, n_sims)
    final_positions = np.random.randint(1, 40, n_sims)

    expected = calculate_expected_points(
        stage1_positions.tolist(),
        stage2_positions.tolist(),
        final_positions.tolist()
    )

    print(f"Expected Stage 1 Points: {expected['expected_stage1_points']:.2f}")
    print(f"Expected Stage 2 Points: {expected['expected_stage2_points']:.2f}")
    print(f"Expected Final Points: {expected['expected_final_points']:.2f}")
    print(f"Expected Total Points: {expected['expected_total_points']:.2f}")
    print(f"\nProbabilities:")
    print(f"  Win Stage 1: {expected['probability_win_stage1']:.1%}")
    print(f"  Win Stage 2: {expected['probability_win_stage2']:.1%}")
    print(f"  Win Race: {expected['probability_win_race']:.1%}")
    print(f"  Top-10 Stage 1: {expected['probability_top10_stage1']:.1%}")
    print(f"  Top-10 Stage 2: {expected['probability_top10_stage2']:.1%}")

    # Test stage points edge cases
    print("\n\nTest 3: Stage Points Edge Cases")
    print("-" * 40)

    test_positions = [1, 5, 10, 11, 20, 40]
    print("Position | Stage Points | Final Points")
    print("---------|--------------|--------------")
    for pos in test_positions:
        stage_pts = _get_stage_points(pos)
        final_pts = _get_final_points(pos)
        print(f"{pos:8} | {stage_pts:12} | {final_pts:12}")
