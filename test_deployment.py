#!/usr/bin/env python3
"""
Quick diagnostic script to verify app can start
Run this locally before deploying to Streamlit Cloud
"""
import sys

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    try:
        from src.simulator import RaceSimulator
        print("  ✓ src.simulator")
    except Exception as e:
        print(f"  ✗ src.simulator: {e}")
        return False

    try:
        from src.monte_carlo import MonteCarloEvaluator
        print("  ✓ src.monte_carlo")
    except Exception as e:
        print(f"  ✗ src.monte_carlo: {e}")
        return False

    try:
        from src.strategy import PRESET_STRATEGIES
        print("  ✓ src.strategy")
    except Exception as e:
        print(f"  ✗ src.strategy: {e}")
        return False

    try:
        from src.sensitivity import StrategySensitivityAnalyzer
        print("  ✓ src.sensitivity")
    except Exception as e:
        print(f"  ✗ src.sensitivity: {e}")
        return False

    return True

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    try:
        from src.simulator import RaceSimulator
        sim = RaceSimulator(num_cars=5, num_laps=10, random_seed=42)
        result = sim.simulate_race()
        print(f"  ✓ Race simulation: {len(result['lap_history'])} laps")
        return True
    except Exception as e:
        print(f"  ✗ Race simulation failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Streamlit Cloud Deployment Diagnostic")
    print("=" * 60)
    print(f"\nPython version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print()

    # Test imports
    imports_ok = test_imports()

    # Test basic functionality
    if imports_ok:
        func_ok = test_basic_functionality()
    else:
        func_ok = False

    print("\n" + "=" * 60)
    if imports_ok and func_ok:
        print("✅ All checks passed! Ready for Streamlit Cloud deployment")
        return 0
    else:
        print("❌ Some checks failed. Fix errors before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
