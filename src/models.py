"""
Caution prediction model using XGBoost.

Trains a classifier to predict whether a caution will occur
in the next N laps based on race state features.
"""
import numpy as np
import pandas as pd
import pickle
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve

# Import XGBoost
try:
    from xgboost import XGBClassifier
except ImportError:
    print("Warning: XGBoost not installed. Install with: pip install xgboost")
    XGBClassifier = None


class CautionPredictor:
    """
    XGBoost-based caution prediction model.

    Predicts probability of caution occurring in next N laps
    based on current race state features.
    """

    def __init__(self,
                 n_estimators: int = 100,
                 max_depth: int = 4,
                 learning_rate: float = 0.05,
                 subsample: float = 0.8,
                 colsample_bytree: float = 0.8,
                 scale_pos_weight: float = 10,
                 random_state: int = 42):
        """
        Initialize model with balanced hyperparameters.

        Args:
            n_estimators: Number of trees
            max_depth: Maximum tree depth
            learning_rate: Step size shrinkage
            subsample: Subsample ratio for training instances
            colsample_bytree: Subsample ratio of columns
            scale_pos_weight: Balances positive/negative samples
            random_state: Random seed
        """
        if XGBClassifier is None:
            raise ImportError("XGBoost is required. Install with: pip install xgboost")

        self.model = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            scale_pos_weight=scale_pos_weight,
            random_state=random_state,
            use_label_encoder=False,
            eval_metric='logloss',
            n_jobs=-1  # Use all available cores
        )

        self.feature_names = None
        self.is_trained = False
        self.training_metrics = {}

    def train(self,
             X: np.ndarray,
             y: np.ndarray,
             feature_names: List[str],
             validation_split: float = 0.2) -> Dict:
        """
        Train model with train/validation split.

        Args:
            X: Feature matrix
            y: Target labels
            feature_names: List of feature names
            validation_split: Fraction of data for validation

        Returns:
            Dict with training metrics
        """
        self.feature_names = feature_names

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )

        print(f"Training set: {len(X_train)} samples ({y_train.mean():.2%} positive)")
        print(f"Validation set: {len(X_val)} samples ({y_val.mean():.2%} positive)")

        # Train model
        print("\nTraining XGBoost model...")
        self.model.fit(X_train, y_train, verbose=False)
        self.is_trained = True

        # Evaluate on train and validation
        train_pred = self.model.predict_proba(X_train)[:, 1]
        val_pred = self.model.predict_proba(X_val)[:, 1]

        # Calculate metrics
        metrics = {
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'train_positive_rate': y_train.mean(),
            'val_positive_rate': y_val.mean(),
            'train_auc': roc_auc_score(y_train, train_pred),
            'val_auc': roc_auc_score(y_val, val_pred),
            'feature_importance': dict(zip(
                feature_names,
                self.model.feature_importances_
            ))
        }

        # Find optimal threshold (maximize F1)
        precision, recall, thresholds = precision_recall_curve(y_val, val_pred)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
        best_idx = np.argmax(f1_scores)
        metrics['optimal_threshold'] = thresholds[best_idx]
        metrics['max_f1'] = f1_scores[best_idx]

        # Calculate classification report at optimal threshold
        y_pred_threshold = (val_pred >= metrics['optimal_threshold']).astype(int)
        report = classification_report(y_val, y_pred_threshold, output_dict=True)
        metrics['classification_report'] = report

        # Store metrics
        self.training_metrics = metrics

        # Print results
        print(f"\n✅ Training Complete!")
        print(f"\n📊 Performance Metrics:")
        print(f"  Train AUC: {metrics['train_auc']:.3f}")
        print(f"  Val AUC: {metrics['val_auc']:.3f}")
        print(f"  Max F1: {metrics['max_f1']:.3f} (threshold: {metrics['optimal_threshold']:.3f})")

        print(f"\n🔍 Top Features:")
        top_features = sorted(
            metrics['feature_importance'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for feature, importance in top_features:
            print(f"  {feature}: {importance:.3f}")

        return metrics

    def predict_caution_probability(self, features: Dict[str, float]) -> float:
        """
        Predict probability of caution in next 5 laps.

        Args:
            features: Dict of feature names to values

        Returns:
            Probability (0-1)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")

        # Ensure feature order matches training
        X = np.array([[features.get(name, 0.0) for name in self.feature_names]])

        # Predict
        prob = self.model.predict_proba(X)[0, 1]

        return prob

    def predict_proba_batch(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probabilities for multiple samples.

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Array of probabilities (n_samples,)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")

        return self.model.predict_proba(X)[:, 1]

    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """
        Get top N most important features.

        Args:
            top_n: Number of features to return

        Returns:
            DataFrame with features and importance scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")

        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance.head(top_n)

    def save(self, path: str):
        """
        Save model to disk.

        Args:
            path: Path to save model
        """
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained,
                'training_metrics': self.training_metrics
            }, f)
        print(f"✅ Model saved to {path}")

    def load(self, path: str):
        """
        Load model from disk.

        Args:
            path: Path to load model from
        """
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.feature_names = data['feature_names']
            self.is_trained = data['is_trained']
            self.training_metrics = data.get('training_metrics', {})
        print(f"✅ Model loaded from {path}")

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Evaluate model on test data.

        Args:
            X: Feature matrix
            y: True labels

        Returns:
            Dict with evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")

        # Predict probabilities
        y_pred_proba = self.predict_proba_batch(X)

        # Calculate metrics
        metrics = {
            'auc': roc_auc_score(y, y_pred_proba),
            'avg_predicted_prob': y_pred_proba.mean(),
            'true_positive_rate': y.mean()
        }

        # Find predictions at optimal threshold
        threshold = self.training_metrics.get('optimal_threshold', 0.5)
        y_pred = (y_pred_proba >= threshold).astype(int)

        # Classification report
        report = classification_report(y, y_pred, output_dict=True, zero_division=0)
        metrics['classification_report'] = report

        return metrics


def train_and_evaluate(data_path: str = 'data/race_data.csv',
                       model_path: str = 'models/caution_predictor.pkl') -> CautionPredictor:
    """
    Complete training pipeline for caution predictor.

    Args:
        data_path: Path to training data
        model_path: Path to save trained model

    Returns:
        Trained CautionPredictor model
    """
    from src.features import prepare_training_data
    import os

    print("=" * 60)
    print("NASCAR Caution Prediction Model - Training Pipeline")
    print("=" * 60)

    # Load data
    print(f"\n📂 Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"  Loaded {len(df)} rows from {df['race_id'].nunique()} races")

    # Prepare features
    print(f"\n🔧 Extracting features...")
    X, y, feature_names = prepare_training_data(df, prediction_horizon=5)

    # Create model
    print(f"\n🤖 Initializing model...")
    predictor = CautionPredictor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=10,
        random_state=42
    )

    # Train
    metrics = predictor.train(X, y, feature_names)

    # Save model
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    predictor.save(model_path)

    # Print feature importance
    print(f"\n📊 Feature Importance (Top 10):")
    importance_df = predictor.get_feature_importance(top_n=10)
    print(importance_df.to_string(index=False))

    return predictor


if __name__ == '__main__':
    # Train model when run directly
    predictor = train_and_evaluate()
