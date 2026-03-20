"""
Strategy definitions and evaluation for NASCAR racing.

Defines preset strategies and utilities for strategy comparison.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
import pandas as pd


@dataclass
class PitStop:
    """
    Pit stop configuration.

    Defines when and how a car pits.
    """
    lap: int
    duration: float = 19.5  # seconds
    fuel_added: float = 100.0  # percentage
    tires_changed: bool = True

    def __repr__(self):
        return f"PitStop(lap={self.lap}, tires={self.tires_changed})"


@dataclass
class Strategy:
    """
    Race strategy defined by sequence of pit stops.

    A strategy defines when and how a car will pit during a race.
    """
    name: str
    description: str
    pit_stops: List[PitStop]

    def __post_init__(self):
        """Sort pit stops by lap"""
        self.pit_stops.sort(key=lambda x: x.lap)

    def get_pit_at_lap(self, lap: int) -> Optional[PitStop]:
        """Return pit stop if scheduled for this lap"""
        for pit in self.pit_stops:
            if pit.lap == lap:
                return pit
        return None

    def should_pit(self, lap: int) -> bool:
        """Check if strategy calls for pit this lap"""
        return self.get_pit_at_lap(lap) is not None

    def get_next_pit_lap(self, current_lap: int) -> Optional[int]:
        """Get next pit lap after current lap"""
        for pit in self.pit_stops:
            if pit.lap > current_lap:
                return pit.lap
        return None

    def __repr__(self):
        pit_laps = [pit.lap for pit in self.pit_stops]
        return f"Strategy('{self.name}', pits={pit_laps})"


# Preset strategies
PRESET_STRATEGIES: Dict[str, Strategy] = {
    'standard': Strategy(
        name='Standard',
        description='Regular pit stops every 50 laps with fuel and tires',
        pit_stops=[
            PitStop(lap=50),
            PitStop(lap=100),
            PitStop(lap=150)
        ]
    ),

    'aggressive': Strategy(
        name='Aggressive',
        description='Delay pits to gain track position, higher variance',
        pit_stops=[
            PitStop(lap=55),
            PitStop(lap=110),
            PitStop(lap=165)
        ]
    ),

    'conservative': Strategy(
        name='Conservative',
        description='Early pit stops for fresh tires, safer strategy',
        pit_stops=[
            PitStop(lap=45),
            PitStop(lap=90),
            PitStop(lap=135)
        ]
    ),

    'two_stop': Strategy(
        name='Two-Stop',
        description='Only two pit stops, must stretch fuel and tires',
        pit_stops=[
            PitStop(lap=67),
            PitStop(lap=133)
        ]
    ),

    'four_stop': Strategy(
        name='Four-Stop',
        description='Four pit stops, always fresh tires',
        pit_stops=[
            PitStop(lap=40),
            PitStop(lap=80),
            PitStop(lap=120),
            PitStop(lap=160)
        ]
    ),

    'late_race_hero': Strategy(
        name='Late Race Hero',
        description='Stay out late, hope for cautions',
        pit_stops=[
            PitStop(lap=30),
            PitStop(lap=90),
            # No third stop - hope for late caution
        ]
    )
}


def create_custom_strategy(name: str,
                          pit_laps: List[int],
                          description: str = "") -> Strategy:
    """
    Create a custom strategy from list of pit laps.

    Args:
        name: Strategy name
        pit_laps: List of lap numbers to pit
        description: Strategy description

    Returns:
        Strategy object
    """
    pit_stops = [PitStop(lap=lap) for lap in pit_laps]
    return Strategy(
        name=name,
        description=description or f"Custom strategy with pits at {pit_laps}",
        pit_stops=pit_stops
    )


def compare_strategy_timelines(strategies: Dict[str, Strategy]) -> pd.DataFrame:
    """
    Create comparison table of strategy pit timelines.

    Args:
        strategies: Dict of strategy name to Strategy

    Returns:
        DataFrame with pit lap comparison
    """
    import pandas as pd

    data = []
    for name, strategy in strategies.items():
        row = {'strategy': name}
        for i in range(4):  # Max 4 pit stops
            if i < len(strategy.pit_stops):
                row[f'pit_{i+1}'] = strategy.pit_stops[i].lap
            else:
                row[f'pit_{i+1}'] = None
        data.append(row)

    df = pd.DataFrame(data).set_index('strategy')
    return df


def calculate_strategy_pit_cost(strategies: Dict[str, Strategy],
                               avg_lap_time: float = 48.0) -> Dict[str, float]:
    """
    Calculate time lost to pit stops for each strategy.

    Args:
        strategies: Dict of strategies
        avg_lap_time: Average lap time for racing (not pitting)

    Returns:
        Dict mapping strategy name to total pit time
    """
    pit_times = {}
    for name, strategy in strategies.items():
        total_pit_time = sum(pit.duration for pit in strategy.pit_stops)
        # Also account for laps spent in pits instead of racing
        laps_pitted = len(strategy.pit_stops)
        opportunity_cost = laps_pitted * avg_lap_time
        pit_times[name] = total_pit_time + opportunity_cost

    return pit_times


def generate_strategy_report(strategies: Dict[str, Strategy]) -> str:
    """
    Generate human-readable strategy report.

    Args:
        strategies: Dict of strategies

    Returns:
        Multi-line string report
    """
    lines = []
    lines.append("=" * 70)
    lines.append("NASCAR Strategy Report")
    lines.append("=" * 70)

    for name, strategy in strategies.items():
        lines.append(f"\n{name}:")
        lines.append(f"  Description: {strategy.description}")
        lines.append(f"  Pit Stops: {len(strategy.pit_stops)}")

        for i, pit in enumerate(strategy.pit_stops, 1):
            lines.append(f"    {i}. Lap {pit.lap} ({'Full service' if pit.tires_changed else 'Fuel only'})")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


if __name__ == '__main__':
    # Test strategy definitions
    print(generate_strategy_report(PRESET_STRATEGIES))

    # Compare timelines
    print("\nStrategy Timeline Comparison:")
    print(compare_strategy_timelines(PRESET_STRATEGIES))

    # Calculate pit costs
    print("\nPit Stop Time Costs:")
    costs = calculate_strategy_pit_cost(PRESET_STRATEGIES)
    for name, cost in costs.items():
        print(f"  {name}: {cost:.1f} seconds")
