"""
Tests for caution prediction features and models.
"""
import pytest
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '.')

from src.features import extract_caution_features, prepare_training_data
from src.models import CautionPredictor


class TestFeatureExtraction:
    """Test feature extraction functions"""

    @pytest.fixture
    def sample_race_data(self):
        """Create sample race data for testing"""
        data = []
        for lap in range(1, 51):
            for car_id in range(1, 11):
                is_caution = 1 if lap in [15, 30, 45] else 0
                data.append({
                    'race_id': 1,
                    'lap': lap,
                    'car_id': car_id,
                    'position': car_id,
                    'lap_time': 48.0 + np.random.normal(0, 0.5),
                    'is_caution_lap': is_caution,
                    'tire_age': (lap % 50),
                    'fuel_level': max(0, 100 - lap * 0.25)
                })
        return pd.DataFrame(data)

    def test_extract_features_mid_race(self, sample_race_data):
        """Test feature extraction at mid-race"""
        features = extract_caution_features(sample_race_data, lap=25)

        # Check basic features
        assert 'race_progress' in features
        assert 'laps_since_last_caution' in features
        assert 'avg_tire_age' in features

        # Check values are reasonable
        assert 0 < features['race_progress'] < 1
        assert features['laps_since_last_caution'] > 0
        assert features['avg_tire_age'] > 0

    def test_extract_features_returns_dict(self, sample_race_data):
        """Test that extract_features returns a dict"""
        features = extract_caution_features(sample_race_data, lap=25)

        assert isinstance(features, dict)
        assert len(features) > 10  # Should have many features

    def test_extract_features_early_lap(self, sample_race_data):
        """Test feature extraction at early lap (no history)"""
        # Lap 5 should have minimal history
        features = extract_caution_features(sample_race_data, lap=5)

        # Should still return dict, possibly with defaults
        assert isinstance(features, dict)

    def test_feature_consistency(self, sample_race_data):
        """Test that features have consistent values"""
        features1 = extract_caution_features(sample_race_data, lap=25)
        features2 = extract_caution_features(sample_race_data, lap=25)

        # Same input should give same output
        for key in features1.keys():
            assert features1[key] == features2[key]

    def test_prepare_training_data(self, sample_race_data):
        """Test training data preparation"""
        X, y, feature_names = prepare_training_data(sample_race_data, prediction_horizon=5)

        # Check shapes
        assert X.ndim == 2
        assert y.ndim == 1
        assert X.shape[0] == y.shape[0]  # Same number of samples
        assert X.shape[1] == len(feature_names)

        # Check labels
        assert set(y).issubset({0, 1})  # Binary labels

    def test_feature_names_consistent(self, sample_race_data):
        """Test that feature names are consistent"""
        _, _, feature_names = prepare_training_data(sample_race_data, prediction_horizon=5)

        # Check no duplicates
        assert len(feature_names) == len(set(feature_names))

        # Check names are strings
        assert all(isinstance(name, str) for name in feature_names)


class TestCautionPredictor:
    """Test caution prediction model"""

    @pytest.fixture
    def sample_training_data(self):
        """Create small sample for training"""
        # Simple synthetic data
        np.random.seed(42)
        X = np.random.randn(100, 10)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)  # Simple rule
        feature_names = [f'feature_{i}' for i in range(10)]
        return X, y, feature_names

    def test_initialize_model(self):
        """Test model initialization"""
        model = CautionPredictor()

        assert model is not None
        assert not model.is_trained

    def test_train_model(self, sample_training_data):
        """Test model training"""
        X, y, feature_names = sample_training_data
        model = CautionPredictor(n_estimators=10)

        metrics = model.train(X, y, feature_names)

        # Check training succeeded
        assert model.is_trained
        assert 'train_auc' in metrics
        assert 'val_auc' in metrics
        assert metrics['train_auc'] > 0.5  # Should learn something

    def test_predict_single(self, sample_training_data):
        """Test single prediction"""
        X, y, feature_names = sample_training_data
        model = CautionPredictor(n_estimators=10)
        model.train(X, y, feature_names)

        # Create feature dict
        features = {name: 0.0 for name in feature_names}

        prob = model.predict_caution_probability(features)

        assert 0 <= prob <= 1  # Valid probability

    def test_predict_batch(self, sample_training_data):
        """Test batch prediction"""
        X, y, feature_names = sample_training_data
        model = CautionPredictor(n_estimators=10)
        model.train(X, y, feature_names)

        probs = model.predict_proba_batch(X)

        assert len(probs) == len(X)
        assert all(0 <= p <= 1 for p in probs)

    def test_feature_importance(self, sample_training_data):
        """Test feature importance extraction"""
        X, y, feature_names = sample_training_data
        model = CautionPredictor(n_estimators=10)
        model.train(X, y, feature_names)

        importance = model.get_feature_importance(top_n=5)

        assert len(importance) <= 5
        assert 'feature' in importance.columns
        assert 'importance' in importance.columns

    def test_save_load_model(self, sample_training_data, tmp_path):
        """Test model saving and loading"""
        X, y, feature_names = sample_training_data
        model = CautionPredictor(n_estimators=10)
        model.train(X, y, feature_names)

        # Get prediction before saving
        features = {name: 0.0 for name in feature_names}
        prob_before = model.predict_caution_probability(features)

        # Save
        save_path = tmp_path / "test_model.pkl"
        model.save(str(save_path))

        # Create new model and load
        model2 = CautionPredictor()
        model2.load(str(save_path))

        # Check prediction matches
        prob_after = model2.predict_caution_probability(features)
        assert prob_before == prob_after

    def test_evaluate_model(self, sample_training_data):
        """Test model evaluation"""
        X, y, feature_names = sample_training_data
        model = CautionPredictor(n_estimators=10)
        model.train(X, y, feature_names)

        metrics = model.evaluate(X, y)

        assert 'auc' in metrics
        assert 'classification_report' in metrics


class TestModelIntegration:
    """Integration tests for full pipeline"""

    def test_end_to_end_training(self, tmp_path):
        """Test complete training pipeline"""
        # Create small synthetic dataset
        data = []
        for lap in range(1, 51):
            for car_id in range(1, 6):
                is_caution = 1 if lap % 15 == 0 else 0
                data.append({
                    'race_id': 1,
                    'lap': lap,
                    'car_id': car_id,
                    'position': car_id,
                    'lap_time': 48.0 + np.random.normal(0, 0.3),
                    'is_caution_lap': is_caution,
                    'tire_age': lap % 50,
                    'fuel_level': max(0, 100 - lap * 0.25)
                })

        df = pd.DataFrame(data)

        # Prepare features
        X, y, feature_names = prepare_training_data(df, prediction_horizon=5)

        # Train model
        model = CautionPredictor(n_estimators=20)
        metrics = model.train(X, y, feature_names)

        # Check training worked
        assert model.is_trained
        assert metrics['val_auc'] > 0.5  # Should learn

    def test_prediction_consistency(self, tmp_path):
        """Test that predictions are consistent"""
        # Create simple dataset
        data = []
        for lap in range(1, 31):
            for car_id in range(1, 4):
                data.append({
                    'race_id': 1,
                    'lap': lap,
                    'car_id': car_id,
                    'position': car_id,
                    'lap_time': 48.0,
                    'is_caution_lap': 0,
                    'tire_age': lap % 50,
                    'fuel_level': 100 - lap * 0.25
                })

        df = pd.DataFrame(data)

        # Prepare features
        X, y, feature_names = prepare_training_data(df, prediction_horizon=5)

        # Train model
        model = CautionPredictor(n_estimators=10)
        model.train(X, y, feature_names)

        # Same features should give same prediction
        features = {name: 0.0 for name in feature_names}
        prob1 = model.predict_caution_probability(features)
        prob2 = model.predict_caution_probability(features)

        assert prob1 == prob2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
