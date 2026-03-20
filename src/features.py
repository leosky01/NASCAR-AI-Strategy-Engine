"""
Feature engineering for caution prediction.

Extracts features from race data to predict whether a caution
will occur in the next N laps.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats


def extract_caution_features(race_df: pd.DataFrame,
                            lap: int,
                            car_id: int = None,
                            window: int = 10) -> Dict[str, float]:
    """
    Extract features for predicting caution probability at a given lap.

    Features capture:
    - Race context (progress, laps remaining)
    - Caution history (frequency, recency)
    - Field competitiveness (lap time variance)
    - Tire wear statistics
    - Position volatility

    Args:
        race_df: DataFrame with race data (must have rows < lap)
        lap: Current lap number
        car_id: Optional car ID for car-specific features
        window: Rolling window for statistics

    Returns:
        Dict of feature names to values
    """
    # Get history up to current lap
    history = race_df[race_df['lap'] < lap].copy()

    # Handle early laps (no history)
    if len(history) == 0 or lap < window:
        return _get_default_features()

    features = {}

    # ===== RACE CONTEXT FEATURES =====
    features['race_progress'] = lap / 200.0  # Normalized 0-1
    features['laps_remaining'] = max(0, 200 - lap)
    features['current_lap_norm'] = lap / 200.0

    # ===== CAUTION HISTORY FEATURES =====
    caution_laps = history[history['is_caution_lap'] == 1]['lap']
    features['cautions_so_far'] = len(caution_laps)
    features['laps_since_last_caution'] = lap - caution_laps.max() if len(caution_laps) > 0 else lap
    features['caution_density'] = len(caution_laps) / max(1, lap)  # Cautions per lap
    features['green_flag_run_length'] = features['laps_since_last_caution']
    features['long_green_flag'] = int(features['green_flag_run_length'] > 40)  # Risk increases

    # ===== FIELD COMPETITIVENESS FEATURES =====
    recent = history[history['lap'] > lap - window]

    # Lap time variance indicates pack racing vs. strung out field
    if 'lap_time' in recent.columns:
        lap_times_by_lap = recent.groupby('lap')['lap_time']
        features['lap_time_variance'] = lap_times_by_lap.std().mean() if len(lap_times_by_lap) > 0 else 0

        # Field spread (time from 1st to last)
        current_lap_data = history[history['lap'] == lap - 1]
        if len(current_lap_data) > 0 and 'lap_time' in current_lap_data.columns:
            features['field_spread'] = current_lap_data['lap_time'].max() - current_lap_data['lap_time'].min()
        else:
            features['field_spread'] = 0.0
    else:
        features['lap_time_variance'] = 0.0
        features['field_spread'] = 0.0

    # ===== TIRE WEAR FEATURES =====
    if 'tire_age' in history.columns:
        current_lap_data = history[history['lap'] == lap - 1]
        if len(current_lap_data) > 0:
            features['avg_tire_age'] = current_lap_data['tire_age'].mean()
            features['max_tire_age'] = current_lap_data['tire_age'].max()
            features['tired_cars_pct'] = (current_lap_data['tire_age'] > 40).mean()  # Cars on old tires
        else:
            features['avg_tire_age'] = 0.0
            features['max_tire_age'] = 0.0
            features['tired_cars_pct'] = 0.0
    else:
        features['avg_tire_age'] = 0.0
        features['max_tire_age'] = 0.0
        features['tired_cars_pct'] = 0.0

    # ===== POSITION VOLATILITY FEATURES =====
    if 'position' in history.columns:
        position_changes = []
        for cid in history['car_id'].unique():
            car_data = history[history['car_id'] == cid].sort_values('lap')
            if len(car_data) > 1:
                changes = abs(car_data['position'].diff().dropna())
                position_changes.extend(changes)

        if position_changes:
            features['avg_position_change'] = np.mean(position_changes)
            features['max_position_change'] = np.max(position_changes)
            features['position_volatility'] = np.std(position_changes)
        else:
            features['avg_position_change'] = 0.0
            features['max_position_change'] = 0.0
            features['position_volatility'] = 0.0
    else:
        features['avg_position_change'] = 0.0
        features['max_position_change'] = 0.0
        features['position_volatility'] = 0.0

    # ===== INTERACTION FEATURES =====
    # Risk accumulates with: old tires + long green flag + late race
    features['risk_accumulation'] = (
        features['avg_tire_age'] / 50.0 *  # Normalized tire age
        features['green_flag_run_length'] / 50.0 *  # Normalized run length
        features['race_progress']  # Late race factor
    )

    # Caution likelihood increases with these factors
    features['caution_likelihood_score'] = (
        features['avg_tire_age'] / 50.0 * 0.3 +
        features['green_flag_run_length'] / 100.0 * 0.3 +
        features['race_progress'] * 0.2 +
        features['position_volatility'] / 10.0 * 0.2
    )

    return features


def _get_default_features() -> Dict[str, float]:
    """Return default features for early laps with no history"""
    return {
        'race_progress': 0.0,
        'laps_remaining': 200,
        'current_lap_norm': 0.0,
        'cautions_so_far': 0,
        'laps_since_last_caution': 0,
        'caution_density': 0.0,
        'green_flag_run_length': 0,
        'long_green_flag': 0,
        'lap_time_variance': 0.0,
        'field_spread': 0.0,
        'avg_tire_age': 0.0,
        'max_tire_age': 0.0,
        'tired_cars_pct': 0.0,
        'avg_position_change': 0.0,
        'max_position_change': 0.0,
        'position_volatility': 0.0,
        'risk_accumulation': 0.0,
        'caution_likelihood_score': 0.0
    }


def prepare_training_data(race_df: pd.DataFrame,
                         prediction_horizon: int = 5) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare training data for caution prediction.

    For each lap in each race, extract features and create a label
    indicating whether a caution occurs in the next N laps.

    Args:
        race_df: Complete race data
        prediction_horizon: Lookahead window (laps)

    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Labels (1 if caution in next horizon, else 0)
        feature_names: List of feature names
    """
    X = []
    y = []
    feature_names = None

    print("Preparing training data...")

    for race_id in race_df['race_id'].unique():
        race = race_df[race_df['race_id'] == race_id]
        max_lap = race['lap'].max()

        # Need at least 10 laps of history
        for lap in range(10, max_lap - prediction_horizon):
            # Extract features
            features = extract_caution_features(race, lap)
            X.append(list(features.values()))

            # Save feature names on first iteration
            if feature_names is None:
                feature_names = list(features.keys())

            # Check for caution in next N laps
            future = race[(race['lap'] >= lap) & (race['lap'] < lap + prediction_horizon)]
            y.append(int(future['is_caution_lap'].any()))

    X = np.array(X)
    y = np.array(y)

    print(f"  Samples: {len(X)}")
    print(f"  Features: {len(feature_names)}")
    print(f"  Positive rate: {y.mean():.2%}")

    return X, y, feature_names


def create_feature_importance_report(model, feature_names: List[str], top_n: int = 15) -> pd.DataFrame:
    """
    Create feature importance report from trained model.

    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        top_n: Number of top features to show

    Returns:
        DataFrame with feature importance
    """
    importances = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    return importances.head(top_n)


def analyze_feature_correlations(X: np.ndarray, feature_names: List[str]) -> pd.DataFrame:
    """
    Analyze correlations between features.

    Args:
        X: Feature matrix
        feature_names: List of feature names

    Returns:
        DataFrame with correlation matrix
    """
    df = pd.DataFrame(X, columns=feature_names)
    return df.corr()
