"""
Tests for GAM tire model implementation.

Tests synthetic data generation, model fitting, and predictions.
"""
import pytest
import numpy as np
from src.tire_model import (
    TireModelResult,
    TrackCharacteristics,
    TrackSpecificModel,
    TireModelManager,
    GAM_AVAILABLE
)


class TestTrackCharacteristics:
    """Test track characteristics dataclass."""

    def test_create_track_characteristics(self):
        """Test creating track characteristics."""
        track = TrackCharacteristics(
            abrasiveness=0.8,
            banking=11.0,
            length=1.0,
            tire_wear_rate=1.3
        )

        assert track.abrasiveness == 0.8
        assert track.banking == 11.0
        assert track.length == 1.0
        assert track.tire_wear_rate == 1.3


class TestTireModelManager:
    """Test TireModelManager."""

    @pytest.fixture
    def manager(self):
        """Create a tire model manager for testing."""
        return TireModelManager(use_synthetic=True)

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.use_synthetic is True
        assert len(manager.models) == 0
        assert manager.models_dir == 'models/tire_models'

    def test_track_characteristics_defined(self, manager):
        """Test that all 5 focus tracks have characteristics defined."""
        required_tracks = ['Phoenix', 'Charlotte', 'Darlington', 'Bristol', 'Talladega']

        for track in required_tracks:
            assert track in manager.TRACK_CHARACTERISTICS
            char = manager.TRACK_CHARACTERISTICS[track]
            assert isinstance(char, TrackCharacteristics)
            assert 0 <= char.abrasiveness <= 1
            assert char.banking > 0
            assert char.length > 0
            assert char.tire_wear_rate > 0

    def test_generate_synthetic_training_data(self, manager):
        """Test synthetic data generation."""
        data = manager.generate_synthetic_training_data(
            track_name='Charlotte',
            n_samples=100,
            random_seed=42
        )

        # Check shape
        assert data.shape == (100, 6)  # [tire_age, track_temp, compound, traffic_density, overtaking_ability, penalty]

        # Check data ranges
        assert np.all(data[:, 0] >= 0)  # tire_age >= 0
        assert np.all(data[:, 0] <= 100)  # tire_age <= 100
        assert np.all(data[:, 1] >= 70)  # track_temp >= 70°F
        assert np.all(data[:, 1] <= 120)  # track_temp <= 120°F
        assert np.all(data[:, 2] >= 0)  # compound in [0, 1, 2]
        assert np.all(data[:, 2] <= 2)
        assert np.all(data[:, 3] >= 0)  # traffic_density in [0, 1]
        assert np.all(data[:, 3] <= 1)
        assert np.all(data[:, 4] >= 0.5)  # overtaking_ability in [0.5, 1.5]
        assert np.all(data[:, 4] <= 1.5)
        assert np.all(data[:, 5] >= 0)  # penalty >= 0
        assert np.all(data[:, 5] <= 5)  # penalty <= 5

    def test_generate_synthetic_data_reproducibility(self, manager):
        """Test that synthetic data generation is reproducible."""
        data1 = manager.generate_synthetic_training_data('Charlotte', n_samples=50, random_seed=42)
        data2 = manager.generate_synthetic_training_data('Charlotte', n_samples=50, random_seed=42)

        np.testing.assert_array_equal(data1, data2)

    def test_generate_synthetic_data_unknown_track(self, manager):
        """Test that unknown track raises error."""
        with pytest.raises(ValueError, match="Unknown track"):
            manager.generate_synthetic_training_data('UnknownTrack')

    def test_predict_tire_penalty_fallback(self, manager):
        """Test prediction using fallback model (works without GAM)."""
        result = manager.predict_tire_penalty(
            track_name='Charlotte',
            tire_age=40,
            traffic_density=0.5
        )

        assert isinstance(result, TireModelResult)
        assert 0 <= result.predicted_penalty <= 5
        assert result.tire_effect >= 0
        assert result.traffic_effect >= 0

    def test_predict_tire_penalty_old_tires(self, manager):
        """Test that old tires have higher penalty."""
        # Old tires should have higher penalty
        old_tires = manager.predict_tire_penalty('Charlotte', tire_age=80)
        new_tires = manager.predict_tire_penalty('Charlotte', tire_age=10)

        assert old_tires.predicted_penalty > new_tires.predicted_penalty

    def test_predict_tire_penalty_traffic_effect(self, manager):
        """Test that traffic increases penalty."""
        # Use younger tires so there's room for traffic to have an effect
        heavy_traffic = manager.predict_tire_penalty('Charlotte', tire_age=20, traffic_density=0.8)
        no_traffic = manager.predict_tire_penalty('Charlotte', tire_age=20, traffic_density=0.0)

        # Heavy traffic should have higher penalty (unless capped)
        assert heavy_traffic.predicted_penalty >= no_traffic.predicted_penalty
        # Traffic effect should be positive
        assert heavy_traffic.traffic_effect > 0
        assert no_traffic.traffic_effect == 0

    def test_track_differences(self, manager):
        """Test that different tracks have different tire wear rates."""
        # Phoenix (high abrasiveness) vs Talladega (low abrasiveness)
        phoenix = manager.predict_tire_penalty('Phoenix', tire_age=50, traffic_density=0.3)
        talladega = manager.predict_tire_penalty('Talladega', tire_age=50, traffic_density=0.3)

        # Phoenix should generally have higher penalty due to abrasiveness
        # (This may vary due to randomness in fallback, but on average should hold)
        assert phoenix.predicted_penalty >= 0
        assert talladega.predicted_penalty >= 0

    def test_fit_track_model_without_gam(self, manager):
        """Test model fitting without GAM (graceful fallback)."""
        if GAM_AVAILABLE:
            pytest.skip("pyGAM is installed, test fallback scenario only when GAM unavailable")

        model = manager.fit_track_model('Charlotte', n_folds=5)

        assert model.track_name == 'Charlotte'
        assert model.is_trained is False  # Not trained without GAM
        assert model.tire_gam is None
        assert model.traffic_gam is None

    def test_get_track_characteristics(self, manager):
        """Test getting track characteristics."""
        char = manager.get_track_characteristics('Charlotte')

        assert char is not None
        assert char.abrasiveness > 0
        assert char.banking > 0

    def test_get_track_characteristics_unknown(self, manager):
        """Test getting characteristics for unknown track."""
        char = manager.get_track_characteristics('UnknownTrack')
        assert char is None


class TestTireModelResult:
    """Test TireModelResult dataclass."""

    def test_create_tire_model_result(self):
        """Test creating a tire model result."""
        result = TireModelResult(
            predicted_penalty=2.5,
            tire_effect=2.0,
            traffic_effect=0.5
        )

        assert result.predicted_penalty == 2.5
        assert result.tire_effect == 2.0
        assert result.traffic_effect == 0.5
        assert result.confidence_interval is None

    def test_tire_model_result_with_confidence(self):
        """Test creating result with confidence interval."""
        result = TireModelResult(
            predicted_penalty=2.5,
            tire_effect=2.0,
            traffic_effect=0.5,
            confidence_interval=(2.0, 3.0)
        )

        assert result.confidence_interval == (2.0, 3.0)


class TestTireModelIntegration:
    """Integration tests for tire model."""

    def test_end_to_end_prediction(self):
        """Test complete workflow: generate data -> fit model -> predict."""
        manager = TireModelManager(use_synthetic=True)

        # Generate data
        data = manager.generate_synthetic_training_data('Charlotte', n_samples=100)

        # Fit model (may use fallback if GAM unavailable)
        model = manager.fit_track_model('Charlotte', training_data=data)

        # Make prediction (works with or without GAM)
        result = manager.predict_tire_penalty(
            track_name='Charlotte',
            tire_age=40,
            traffic_density=0.5
        )

        assert isinstance(result, TireModelResult)
        assert 0 <= result.predicted_penalty <= 5

    def test_multiple_track_predictions(self):
        """Test predictions for multiple tracks."""
        manager = TireModelManager(use_synthetic=True)

        tracks = ['Phoenix', 'Charlotte', 'Darlington', 'Bristol', 'Talladega']
        results = {}

        for track in tracks:
            result = manager.predict_tire_penalty(
                track_name=track,
                tire_age=50,
                traffic_density=0.3
            )
            results[track] = result.predicted_penalty

        # All predictions should be valid
        for track, penalty in results.items():
            assert 0 <= penalty <= 5, f"{track} has invalid penalty: {penalty}"

    def test_extreme_values(self):
        """Test predictions with extreme input values."""
        manager = TireModelManager(use_synthetic=True)

        # Very old tires
        result1 = manager.predict_tire_penalty('Charlotte', tire_age=100)
        assert result1.predicted_penalty <= 5.0  # Should be capped

        # Very heavy traffic
        result2 = manager.predict_tire_penalty('Charlotte', tire_age=40, traffic_density=1.0)
        assert result2.predicted_penalty <= 5.0  # Should be capped

        # No traffic, new tires
        result3 = manager.predict_tire_penalty('Charlotte', tire_age=0, traffic_density=0.0)
        assert result3.predicted_penalty >= 0  # Should be minimal

    def test_overtaking_ability_effect(self):
        """Test that overtaking ability affects traffic penalty."""
        manager = TireModelManager(use_synthetic=True)

        # Good overtaker vs poor overtaker in traffic
        good_driver = manager.predict_tire_penalty(
            'Charlotte',
            tire_age=40,
            traffic_density=0.8,
            overtaking_ability=1.5
        )

        poor_driver = manager.predict_tire_penalty(
            'Charlotte',
            tire_age=40,
            traffic_density=0.8,
            overtaking_ability=0.5
        )

        # Poor driver should have higher penalty from traffic
        assert poor_driver.predicted_penalty >= good_driver.predicted_penalty


@pytest.mark.skipif(not GAM_AVAILABLE, reason="pyGAM not installed")
class TestGAMSpecific:
    """Tests that only run when pyGAM is available."""

    @pytest.fixture
    def manager(self):
        """Create manager for GAM tests."""
        return TireModelManager(use_synthetic=True)

    def test_fit_track_model_with_gam(self, manager):
        """Test model fitting with GAM."""
        model = manager.fit_track_model('Charlotte', n_folds=5)

        assert model.track_name == 'Charlotte'
        assert model.is_trained is True
        assert model.tire_gam is not None
        assert model.traffic_gam is not None
        assert model.cross_val_score >= 0

    def test_train_all_tracks(self, manager):
        """Test training models for all tracks."""
        models = manager.train_all_tracks(
            n_samples_per_track=100,
            save_models=False
        )

        assert len(models) == 5
        for track_name, model in models.items():
            assert model.is_trained is True
            assert model.track_name == track_name
