#!/usr/bin/env python3
"""
Initialize GAM models for all tracks with synthetic data.

This script trains GAM tire models for all 5 focus tracks using
synthetically generated training data.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tire_model import TireModelManager, GAM_AVAILABLE


def main():
    """Initialize GAM models for all tracks."""
    print("=" * 70)
    print("NASCAR Strategy Engine - GAM Model Initialization")
    print("=" * 70)

    if not GAM_AVAILABLE:
        print("\n⚠️  WARNING: pyGAM is not installed!")
        print("   The tire model will fall back to the exponential model.")
        print("   To use GAM models, install with: pip install pygam")
        print("\n   Continuing with synthetic data generation for testing...")
        print()

    # Create tire model manager
    manager = TireModelManager(use_synthetic=True)

    # Available tracks
    tracks = ['Phoenix', 'Charlotte', 'Darlington', 'Bristol', 'Talladega']

    print(f"\nTraining models for {len(tracks)} tracks:")
    print("-" * 70)

    # Train model for each track
    trained_models = {}
    for track in tracks:
        print(f"\n{track}:")
        print(f"  Characteristics: ", end="")

        char = manager.get_track_characteristics(track)
        if char:
            print(f"abrasiveness={char.abrasiveness:.2f}, banking={char.banking}°")

        # Generate training data
        print(f"  Generating {manager.models_dir or 'synthetic'} training data...", end=" ")
        training_data = manager.generate_synthetic_training_data(
            track,
            n_samples=1000,
            random_seed=42
        )
        print(f"✓ ({len(training_data)} samples)")

        # Fit model
        print(f"  Fitting GAM model...", end=" ")
        try:
            model = manager.fit_track_model(track, training_data=training_data, n_folds=5)

            if model.is_trained:
                print(f"✓ (CV score: {model.cross_val_score:.4f})")
                trained_models[track] = model
            else:
                print(f"⚠ (GAM not available, using fallback)")

        except Exception as e:
            print(f"✗ (Error: {e})")

    # Save models
    print("\n" + "=" * 70)
    print("Saving Models")
    print("=" * 70)

    if GAM_AVAILABLE:
        # Create models directory
        os.makedirs('models/tire_models', exist_ok=True)

        for track_name, model in trained_models.items():
            if model.is_trained:
                try:
                    manager.save_model(track_name)
                    print(f"✓ Saved {track_name} model")
                except Exception as e:
                    print(f"✗ Failed to save {track_name}: {e}")
    else:
        print("\n⚠️  Models not saved (pyGAM not installed)")
        print("   The fallback exponential model will be used instead")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    print(f"\nTracks: {len(tracks)}")
    print(f"Trained: {len(trained_models)}")

    if GAM_AVAILABLE:
        print("\n✓ GAM models initialized successfully")
        print("  Location: models/tire_models/")
        print("\nTo use these models in simulations:")
        print("  from src.tire_model import TireModelManager")
        print("  manager = TireModelManager()")
        print("  manager.load_model('Charlotte')")
        print("  simulator.set_tire_model_manager(manager)")
    else:
        print("\n⚠️  GAM models not available (pyGAM not installed)")
        print("   The engine will use the fallback exponential model")
        print("\nTo install GAM support:")
        print("   pip install pygam scikit-learn")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
