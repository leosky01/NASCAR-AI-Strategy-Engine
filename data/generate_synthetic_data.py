"""
Generate synthetic NASCAR race data for training.

Creates realistic race data with caution events for training
the caution prediction model.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class RaceConfig:
    """Configuration for synthetic race generation"""
    num_races: int = 100
    laps_per_race: int = 200
    cars_per_race: int = 40
    caution_base_prob: float = 0.015
    caution_duration_laps: int = 4


class SyntheticDataGenerator:
    """
    Generate synthetic NASCAR race data with realistic caution patterns.

    Caution probability increases with:
    - Tire age (worn tires = more incidents)
    - Race progress (later race = more desperation)
    - Green flag run length (longer = more likely)
    """

    def __init__(self, config: RaceConfig, random_seed: int = 42):
        self.config = config
        self.rng = np.random.RandomState(random_seed)

    def generate_race(self, race_id: int) -> pd.DataFrame:
        """
        Generate a single race with caution events.

        Args:
            race_id: Unique identifier for this race

        Returns:
            DataFrame with lap-by-lap data for all cars
        """
        data = []
        caution_active = False
        caution_remaining = 0
        caution_laps = set()

        # Determine when cautions will occur (for this race)
        caution_schedule = self._generate_caution_schedule()

        for lap in range(1, self.config.laps_per_race + 1):
            # Check if new caution starts this lap
            if lap in caution_schedule and not caution_active:
                caution_active = True
                caution_remaining = self.config.caution_duration_laps
                caution_laps.update(range(lap, lap + self.config.caution_duration_laps))

            # Update caution status
            if caution_active:
                caution_remaining -= 1
                if caution_remaining <= 0:
                    caution_active = False

            is_caution_lap = lap in caution_laps

            # Generate data for each car
            for car_id in range(1, self.config.cars_per_race + 1):
                # Base lap time with some variation
                base_time = 48.0 + self.rng.normal(0, 0.5)

                # Modify based on position (leaders slightly faster)
                position_adjustment = self.rng.exponential(0.1) * (car_id / 40)

                # Caution slowdown
                caution_multiplier = 1.25 if is_caution_lap else 1.0

                lap_time = (base_time + position_adjustment) * caution_multiplier
                lap_time = max(45.0, min(65.0, lap_time))

                # Tire age (simplified - resets periodically)
                tire_age = (lap % 50) if lap > 0 else 0

                # Fuel level
                fuel_level = max(0, 100 - lap * 0.25)

                data.append({
                    'race_id': race_id,
                    'lap': lap,
                    'car_id': car_id,
                    'position': car_id,  # Simplified - no actual racing yet
                    'lap_time': lap_time,
                    'is_caution_lap': int(is_caution_lap),
                    'tire_age': tire_age,
                    'fuel_level': fuel_level,
                    'caught_caution': int(is_caution_lap and car_id == 1)  # Did car 1 cause it?
                })

        return pd.DataFrame(data)

    def _generate_caution_schedule(self) -> List[int]:
        """
        Generate random caution laps for this race.

        Caution probability increases with:
        - Lap number (later laps = more likely)
        - Stochastic element
        """
        caution_laps = []
        lap = 1

        while lap < self.config.laps_per_race:
            # Base probability increases with lap number
            base_prob = self.config.caution_base_prob * (1 + lap / 100)

            # Add some randomness
            if self.rng.random() < base_prob:
                caution_laps.append(lap)
                lap += self.config.caution_duration_laps  # Skip caution laps
            else:
                lap += 1

        return caution_laps

    def generate_dataset(self) -> pd.DataFrame:
        """
        Generate complete dataset with multiple races.

        Returns:
            DataFrame with all race data
        """
        print(f"Generating {self.config.num_races} races...")

        all_data = []
        for race_id in range(1, self.config.num_races + 1):
            if race_id % 10 == 0:
                print(f"  Race {race_id}/{self.config.num_races}")
            race_data = self.generate_race(race_id)
            all_data.append(race_data)

        df = pd.concat(all_data, ignore_index=True)

        print(f"\nGenerated {len(df)} total rows")
        print(f"  Caution laps: {df['is_caution_lap'].sum()} ({df['is_caution_lap'].mean():.2%})")
        print(f"  Races: {df['race_id'].nunique()}")

        return df


def main():
    """Generate synthetic data and save to CSV"""
    import os

    # Create data directory
    os.makedirs('data', exist_ok=True)

    # Generate data
    config = RaceConfig(
        num_races=100,
        laps_per_race=200,
        cars_per_race=40
    )

    generator = SyntheticDataGenerator(config)
    df = generator.generate_dataset()

    # Save to CSV
    output_path = 'data/race_data.csv'
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved to {output_path}")

    # Print statistics
    print("\n📊 Dataset Statistics:")
    print(f"  Total rows: {len(df)}")
    print(f"  Caution rate: {df['is_caution_lap'].mean():.2%}")
    print(f"  Avg cautions per race: {df.groupby('race_id')['is_caution_lap'].max().mean():.1f}")
    print(f"  Lap time range: {df['lap_time'].min():.1f} - {df['lap_time'].max():.1f}s")
    print(f"  Avg lap time: {df['lap_time'].mean():.2f}s")


if __name__ == '__main__':
    main()
