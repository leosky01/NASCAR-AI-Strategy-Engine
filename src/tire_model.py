"""
GAM-based tire degradation and traffic model for NASCAR racing.

Uses Generalized Additive Models (GAMs) to model:
1. Tire degradation based on tire age, track temperature, and compound
2. Traffic effects based on traffic density and overtaking ability

Two-stage approach:
1. Stage 1: Fit GAM to tire falloff
2. Stage 2: Fit GAM to residuals for traffic effects
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pickle
import os

# Optional GAM support - gracefully degrade if not installed
try:
    from pygam import GAM, s, f, LinearGAM
    GAM_AVAILABLE = True
except ImportError:
    GAM_AVAILABLE = False
    # Create dummy classes for type hints
    class GAM:
        pass


@dataclass
class TireModelResult:
    """Result from tire model prediction."""
    predicted_penalty: float
    tire_effect: float  # From tire GAM
    traffic_effect: float  # From traffic GAM
    confidence_interval: Optional[Tuple[float, float]] = None


@dataclass
class TrackCharacteristics:
    """Physical characteristics of a NASCAR track."""
    abrasiveness: float  # 0-1, how abrasive surface is
    banking: float  # degrees
    length: float  # miles
    tire_wear_rate: float  # Multiplier for tire degradation


@dataclass
class TrackSpecificModel:
    """GAM model trained for a specific track."""
    track_name: str
    tire_gam: Optional[GAM]  # Tire degradation model
    traffic_gam: Optional[GAM]  # Traffic effects model
    is_trained: bool = False
    cross_val_score: float = 0.0
    characteristics: Optional[TrackCharacteristics] = None

    def save(self, filepath: str):
        """Save model to file."""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str) -> 'TrackSpecificModel':
        """Load model from file."""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


class TireModelManager:
    """
    Manages GAM-based tire models for multiple tracks.

    Generates synthetic training data and fits track-specific models.
    """

    # Track characteristics for 5 focus tracks
    TRACK_CHARACTERISTICS = {
        'Phoenix': TrackCharacteristics(
            abrasiveness=0.8,
            banking=11.0,
            length=1.0,
            tire_wear_rate=1.3
        ),
        'Charlotte': TrackCharacteristics(
            abrasiveness=0.6,
            banking=24.0,
            length=1.5,
            tire_wear_rate=1.0
        ),
        'Darlington': TrackCharacteristics(
            abrasiveness=0.95,
            banking=25.0,
            length=1.366,
            tire_wear_rate=1.5
        ),
        'Bristol': TrackCharacteristics(
            abrasiveness=0.85,
            banking=26.0,
            length=0.533,
            tire_wear_rate=1.4
        ),
        'Talladega': TrackCharacteristics(
            abrasiveness=0.3,
            banking=33.0,
            length=2.66,
            tire_wear_rate=0.6
        )
    }

    def __init__(self, use_synthetic: bool = True, models_dir: str = 'models/tire_models'):
        """
        Initialize tire model manager.

        Args:
            use_synthetic: If True, generate synthetic data instead of loading real data
            models_dir: Directory to save/load trained models
        """
        self.use_synthetic = use_synthetic
        self.models_dir = models_dir
        self.models: Dict[str, TrackSpecificModel] = {}

        # Create models directory if it doesn't exist
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        if not GAM_AVAILABLE:
            print("Warning: pyGAM not installed. Tire model will fall back to exponential model.")

    def generate_synthetic_training_data(self,
                                       track_name: str,
                                       n_samples: int = 1000,
                                       random_seed: Optional[int] = None) -> np.ndarray:
        """
        Generate synthetic training data for a track.

        Creates realistic tire degradation data based on track characteristics.

        Args:
            track_name: Name of the track
            n_samples: Number of samples to generate
            random_seed: For reproducibility

        Returns:
            Array with columns: [tire_age, track_temp, compound, traffic_density, overtaking_ability, penalty]
        """
        if track_name not in self.TRACK_CHARACTERISTICS:
            raise ValueError(f"Unknown track: {track_name}. Available: {list(self.TRACK_CHARACTERISTICS.keys())}")

        rng = np.random.RandomState(random_seed)
        track = self.TRACK_CHARACTERISTICS[track_name]

        # Generate features
        tire_age = rng.randint(0, 100, n_samples)  # 0-100 laps on tires
        track_temp = rng.uniform(70, 120, n_samples)  # 70-120°F
        compound = rng.randint(0, 3, n_samples)  # 0=soft, 1=medium, 2=hard
        traffic_density = rng.uniform(0, 1, n_samples)  # 0-1 (none to heavy)
        overtaking_ability = rng.uniform(0.5, 1.5, n_samples)  # Driver skill

        # Compound multipliers
        compound_effects = {0: 1.3, 1: 1.0, 2: 0.7}  # soft, medium, hard
        compound_multiplier = np.array([compound_effects[c] for c in compound])

        # Base tire falloff with track abrasiveness
        # Non-linear: accelerates as tires age
        base_falloff = (
            0.08 * tire_age * (1 + track.abrasiveness) *
            (1 + 0.02 * tire_age)  # Acceleration factor
        )

        # Temperature effect (hotter = faster degradation)
        temp_effect = (track_temp - 70) / 50.0  # 0-1

        # Compound effect
        compound_effect = compound_multiplier * base_falloff

        # Traffic effect (dirty air)
        traffic_penalty = traffic_density * 2.0 / overtaking_ability

        # Total penalty with noise
        total_penalty = (
            compound_effect * (1 + temp_effect) +
            traffic_penalty +
            rng.normal(0, 0.5, n_samples)  # Measurement noise
        )

        # Cap at realistic maximum
        total_penalty = np.clip(total_penalty, 0, 5.0)

        # Combine into dataset
        data = np.column_stack([
            tire_age,
            track_temp,
            compound,
            traffic_density,
            overtaking_ability,
            total_penalty
        ])

        return data

    def fit_track_model(self,
                       track_name: str,
                       training_data: Optional[np.ndarray] = None,
                       n_folds: int = 5) -> TrackSpecificModel:
        """
        Fit GAM models for a specific track.

        Two-stage approach:
        1. Fit tire degradation GAM: penalty ~ s(tire_age) + s(track_temp) + f(compound)
        2. Fit traffic GAM on residuals: residual ~ s(traffic_density) + s(overtaking_ability)

        Args:
            track_name: Name of the track
            training_data: Optional pre-generated training data
            n_folds: Number of cross-validation folds

        Returns:
            TrackSpecificModel with trained GAMs
        """
        if not GAM_AVAILABLE:
            # Return untrained model (will fall back to exponential)
            return TrackSpecificModel(
                track_name=track_name,
                tire_gam=None,
                traffic_gam=None,
                is_trained=False,
                characteristics=self.TRACK_CHARACTERISTICS.get(track_name)
            )

        # Generate or use provided training data
        if training_data is None:
            training_data = self.generate_synthetic_training_data(track_name)

        # Extract features
        tire_age = training_data[:, 0]
        track_temp = training_data[:, 1]
        compound = training_data[:, 2].astype(int)
        traffic_density = training_data[:, 3]
        overtaking_ability = training_data[:, 4]
        penalty = training_data[:, 5]

        # Stage 1: Fit tire degradation model
        # penalty ~ s(tire_age) + s(track_temp) + f(compound)
        tire_gam = LinearGAM(
            s(0, n_splines=10) +  # tire_age
            s(1, n_splines=5) +    # track_temp
            f(2)                    # compound (factor)
        )

        tire_gam.fit(
            np.column_stack([tire_age, track_temp, compound]),
            penalty
        )

        # Calculate residuals
        tire_predictions = tire_gam.predict(
            np.column_stack([tire_age, track_temp, compound])
        )
        residuals = penalty - tire_predictions

        # Stage 2: Fit traffic model on residuals
        # residual ~ s(traffic_density) + s(overtaking_ability)
        traffic_gam = LinearGAM(
            s(0, n_splines=5) +  # traffic_density
            s(1, n_splines=5)     # overtaking_ability
        )

        traffic_gam.fit(
            np.column_stack([traffic_density, overtaking_ability]),
            residuals
        )

        # Calculate cross-validation score
        cv_score = tire_gam.statistics_['GCV'] if hasattr(tire_gam, 'statistics_') else 0.0

        # Create and store model
        model = TrackSpecificModel(
            track_name=track_name,
            tire_gam=tire_gam,
            traffic_gam=traffic_gam,
            is_trained=True,
            cross_val_score=cv_score,
            characteristics=self.TRACK_CHARACTERISTICS.get(track_name)
        )

        self.models[track_name] = model

        return model

    def predict_tire_penalty(self,
                           track_name: str,
                           tire_age: float,
                           traffic_density: float = 0.0,
                           track_temp: float = 85.0,
                           compound: int = 1,
                           overtaking_ability: float = 1.0) -> TireModelResult:
        """
        Predict tire penalty using GAM models.

        Args:
            track_name: Name of the track
            tire_age: Age of tires in laps
            traffic_density: Traffic density (0-1)
            track_temp: Track temperature in °F
            compound: Tire compound (0=soft, 1=medium, 2=hard)
            overtaking_ability: Driver's overtaking ability

        Returns:
            TireModelResult with predicted penalty
        """
        # Use exponential fallback if GAM not available or model not trained
        if not GAM_AVAILABLE or track_name not in self.models or not self.models[track_name].is_trained:
            # Fallback to exponential model
            degradation_factor = 1 - np.exp(-tire_age / 20.0)
            base_penalty = 0.08 * tire_age * (1 + degradation_factor)
            traffic_penalty = traffic_density * 2.0 / overtaking_ability
            total_penalty = min(base_penalty + traffic_penalty, 5.0)

            return TireModelResult(
                predicted_penalty=total_penalty,
                tire_effect=base_penalty,
                traffic_effect=traffic_penalty
            )

        model = self.models[track_name]

        # Predict tire effect
        tire_effect = model.tire_gam.predict(np.array([[tire_age, track_temp, compound]]))[0]

        # Predict traffic effect
        traffic_effect = model.traffic_gam.predict(np.array([[traffic_density, overtaking_ability]]))[0]

        # Total penalty
        total_penalty = min(tire_effect + traffic_effect, 5.0)

        return TireModelResult(
            predicted_penalty=total_penalty,
            tire_effect=tire_effect,
            traffic_effect=traffic_effect
        )

    def save_model(self, track_name: str, filepath: Optional[str] = None):
        """
        Save trained model to file.

        Args:
            track_name: Name of the track
            filepath: Optional custom filepath
        """
        if track_name not in self.models:
            raise ValueError(f"No model trained for {track_name}")

        if filepath is None:
            filepath = os.path.join(self.models_dir, f"{track_name}.pkl")

        self.models[track_name].save(filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, track_name: str, filepath: Optional[str] = None) -> TrackSpecificModel:
        """
        Load trained model from file.

        Args:
            track_name: Name of the track
            filepath: Optional custom filepath

        Returns:
            TrackSpecificModel
        """
        if filepath is None:
            filepath = os.path.join(self.models_dir, f"{track_name}.pkl")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        model = TrackSpecificModel.load(filepath)
        self.models[track_name] = model

        return model

    def train_all_tracks(self,
                        n_samples_per_track: int = 1000,
                        n_folds: int = 5,
                        save_models: bool = True) -> Dict[str, TrackSpecificModel]:
        """
        Train models for all available tracks.

        Args:
            n_samples_per_track: Number of synthetic samples per track
            n_folds: Cross-validation folds
            save_models: Whether to save trained models

        Returns:
            Dict mapping track names to trained models
        """
        trained_models = {}

        for track_name in self.TRACK_CHARACTERISTICS.keys():
            print(f"\nTraining model for {track_name}...")

            # Generate training data
            training_data = self.generate_synthetic_training_data(
                track_name,
                n_samples=n_samples_per_track
            )

            # Fit model
            model = self.fit_track_model(
                track_name,
                training_data=training_data,
                n_folds=n_folds
            )

            if model.is_trained:
                print(f"  ✓ Model trained successfully (CV score: {model.cross_val_score:.4f})")
            else:
                print(f"  ⚠ Model not trained (GAM not available)")

            # Save model
            if save_models and model.is_trained:
                self.save_model(track_name)

            trained_models[track_name] = model

        return trained_models

    def get_track_characteristics(self, track_name: str) -> Optional[TrackCharacteristics]:
        """Get physical characteristics for a track."""
        return self.TRACK_CHARACTERISTICS.get(track_name)


if __name__ == '__main__':
    # Test tire model
    print("Testing GAM Tire Model")
    print("=" * 60)

    manager = TireModelManager(use_synthetic=True)

    if not GAM_AVAILABLE:
        print("\nNote: pyGAM not installed. Using fallback exponential model.")
        print("Install with: pip install pygam")
    else:
        print("\n✓ pyGAM is available")

        # Test training for one track
        print("\n\nTest 1: Train Model for Charlotte")
        print("-" * 40)

        model = manager.fit_track_model('Charlotte', n_folds=5)

        if model.is_trained:
            print(f"Track: {model.track_name}")
            print(f"Trained: {model.is_trained}")
            print(f"CV Score: {model.cross_val_score:.4f}")
            print(f"Characteristics: {model.characteristics}")

        # Test prediction
        print("\n\nTest 2: Predict Tire Penalty")
        print("-" * 40)

        result = manager.predict_tire_penalty(
            track_name='Charlotte',
            tire_age=40,
            traffic_density=0.5,
            track_temp=85.0,
            compound=1,
            overtaking_ability=1.0
        )

        print(f"Predicted Penalty: {result.predicted_penalty:.3f} seconds")
        print(f"Tire Effect: {result.tire_effect:.3f} seconds")
        print(f"Traffic Effect: {result.traffic_effect:.3f} seconds")

        # Test track differences
        print("\n\nTest 3: Track-Specific Models")
        print("-" * 40)

        for track in ['Phoenix', 'Talladega']:
            result = manager.predict_tire_penalty(
                track_name=track,
                tire_age=50,
                traffic_density=0.3
            )
            print(f"{track:12} (50 lap tires): {result.predicted_penalty:.3f}s penalty")

    # Test fallback model (works without GAM)
    print("\n\nTest 4: Fallback Model (always available)")
    print("-" * 40)

    result = manager.predict_tire_penalty(
        track_name='UnknownTrack',  # Will use fallback
        tire_age=40,
        traffic_density=0.5
    )

    print(f"Predicted Penalty: {result.predicted_penalty:.3f} seconds")
    print("(Using exponential fallback model)")
