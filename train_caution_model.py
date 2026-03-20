"""
Fast training script for caution prediction model.

Samples data for faster training during development.
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from src.features import prepare_training_data
from src.models import CautionPredictor
import os

print("=" * 60)
print("NASCAR Caution Prediction Model - Fast Training")
print("=" * 60)

# Load data
print(f"\n📂 Loading data...")
df = pd.read_csv('data/race_data.csv')
print(f"  Full dataset: {len(df)} rows")

# Sample for faster training
SAMPLE_SIZE = 10000  # Adjust based on needs
if len(df) > SAMPLE_SIZE:
    print(f"  ⚡ Sampling {SAMPLE_SIZE} rows for faster training")
    # Sample evenly across races
    races = df['race_id'].unique()
    sampled_races = np.random.choice(races, size=min(20, len(races)), replace=False)
    df = df[df['race_id'].isin(sampled_races)]
    print(f"  Using {len(df)} rows from {len(sampled_races)} races")

# Prepare features
print(f"\n🔧 Preparing features...")
X, y, feature_names = prepare_training_data(df, prediction_horizon=5)

# Create model
print(f"\n🤖 Initializing XGBoost model...")
predictor = CautionPredictor(
    n_estimators=50,  # Fewer trees for faster training
    max_depth=4,
    learning_rate=0.05,
    scale_pos_weight=10,
    random_state=42
)

# Train
print(f"\n🏋️ Training model...")
metrics = predictor.train(X, y, feature_names)

# Save model
os.makedirs('models', exist_ok=True)
model_path = 'models/caution_predictor.pkl'
predictor.save(model_path)

# Print summary
print(f"\n✅ Training Complete!")
print(f"\n📊 Final Metrics:")
print(f"  Validation AUC: {metrics['val_auc']:.3f}")
print(f"  Max F1 Score: {metrics['max_f1']:.3f}")
print(f"  Optimal Threshold: {metrics['optimal_threshold']:.3f}")
print(f"\n  Model saved to: {model_path}")

# Test prediction
print(f"\n🧪 Testing prediction...")
test_features = {
    'race_progress': 0.5,
    'laps_since_last_caution': 25,
    'avg_tire_age': 35.0,
    'green_flag_run_length': 25,
    'caution_density': 0.1
}

# Add remaining features
for feature in feature_names:
    if feature not in test_features:
        test_features[feature] = 0.0

prob = predictor.predict_caution_probability(test_features)
print(f"  Caution probability: {prob:.2%}")
