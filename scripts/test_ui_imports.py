"""
Test UI imports and basic functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 80)
print("Testing UI Imports")
print("=" * 80)
print()

# Test 1: Import strategies
print("1. Testing strategy imports...")
try:
    from auronai.strategies import (
        LongMomentumStrategy,
        ShortMomentumStrategy,
        NeutralStrategy,
        SwingTPStrategy,
        StrategyParams,
        RegimeEngine
    )
    print("   ✅ All strategies imported successfully")
except Exception as e:
    print(f"   ❌ Error importing strategies: {e}")
    sys.exit(1)

# Test 2: Import backtesting
print("2. Testing backtesting imports...")
try:
    from auronai.backtesting import (
        BacktestRunner,
        BacktestConfig,
        RunManager
    )
    print("   ✅ Backtesting components imported successfully")
except Exception as e:
    print(f"   ❌ Error importing backtesting: {e}")
    sys.exit(1)

# Test 3: Import data components
print("3. Testing data imports...")
try:
    from auronai.data.parquet_cache import ParquetCache
    from auronai.data.feature_store import FeatureStore
    print("   ✅ Data components imported successfully")
except Exception as e:
    print(f"   ❌ Error importing data components: {e}")
    sys.exit(1)

# Test 4: Create strategy instances
print("4. Testing strategy instantiation...")
try:
    params = StrategyParams(
        top_k=3,
        holding_days=10,
        tp_multiplier=1.05,
        risk_budget=0.20,
        defensive_risk_budget=0.05
    )
    
    long_strat = LongMomentumStrategy(params)
    short_strat = ShortMomentumStrategy(params)
    neutral_strat = NeutralStrategy(params)
    swing_strat = SwingTPStrategy(params)
    
    print(f"   ✅ Long Momentum: {long_strat.name}")
    print(f"   ✅ Short Momentum: {short_strat.name}")
    print(f"   ✅ Neutral: {neutral_strat.name}")
    print(f"   ✅ Swing TP: {swing_strat.name}")
except Exception as e:
    print(f"   ❌ Error creating strategies: {e}")
    sys.exit(1)

# Test 5: Check database
print("5. Testing database connection...")
try:
    run_manager = RunManager(db_path="data/runs.db")
    runs = run_manager.list_runs(limit=5)
    print(f"   ✅ Database connected, found {len(runs)} runs")
    run_manager.close()
except Exception as e:
    print(f"   ❌ Error connecting to database: {e}")
    sys.exit(1)

# Test 6: Check UI pages
print("6. Testing UI page imports...")
try:
    from auronai.ui.pages import run_backtest, view_results, compare_runs
    print("   ✅ All UI pages imported successfully")
except Exception as e:
    print(f"   ❌ Error importing UI pages: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("✅ ALL TESTS PASSED")
print("=" * 80)
print()
print("The UI should work correctly. Try running:")
print("  uv run streamlit run src/auronai/ui/app.py")
print()
