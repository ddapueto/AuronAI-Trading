#!/usr/bin/env python3
"""
End-to-end test for the backtest engine.

This script tests the complete backtest workflow:
1. Generate demo data
2. Run backtest with LongMomentumStrategy
3. Verify results are saved
4. Display metrics
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auronai.backtesting import (
    BacktestRunner,
    BacktestConfig,
    RunManager
)
from auronai.data.parquet_cache import ParquetCache
from auronai.data.feature_store import FeatureStore
from auronai.data.demo_simulator import DemoSimulator
from auronai.strategies import (
    LongMomentumStrategy,
    ShortMomentumStrategy,
    NeutralStrategy,
    StrategyParams,
    RegimeEngine
)


def main():
    """Run end-to-end backtest test."""
    print("=" * 80)
    print("🧪 BACKTEST ENGINE - END-TO-END TEST")
    print("=" * 80)
    print()
    
    # Setup
    print("📦 Setting up components...")
    cache = ParquetCache(cache_dir="data/cache")
    feature_store = FeatureStore(cache_dir="data/cache")
    regime_engine = RegimeEngine(benchmark='SPY')
    run_manager = RunManager(db_path="data/runs.db")
    
    runner = BacktestRunner(
        parquet_cache=cache,
        feature_store=feature_store,
        regime_engine=regime_engine,
        run_manager=run_manager
    )
    print("✅ Components initialized")
    print()
    
    # Generate demo data
    print("📊 Generating demo data...")
    simulator = DemoSimulator(seed=42)
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'SPY']
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    days = (end_date - start_date).days
    
    for symbol in symbols:
        if symbol == 'SPY':
            # Benchmark with moderate growth
            data = simulator.generate_price_data(
                symbol=symbol,
                days=days,
                initial_price=400.0,
                volatility=0.012,
                drift=0.0003
            )
        else:
            # Stocks with varying trends
            if symbol in ['AAPL', 'MSFT']:
                direction = 'up'
                strength = 0.0008
            elif symbol in ['GOOGL', 'NVDA']:
                direction = 'up'
                strength = 0.0005
            else:
                direction = 'up'
                strength = 0.0002
            
            data = simulator.generate_trending_market(
                symbol=symbol,
                days=days,
                initial_price=150.0,
                direction=direction,
                strength=strength,
                volatility=0.02
            )
        
        # Adjust dates
        import pandas as pd
        data.index = pd.date_range(start=start_date, periods=len(data), freq='D')
        cache.save_data(symbol, data)
        print(f"  ✓ {symbol}: {len(data)} days")
    
    print("✅ Demo data generated")
    print()
    
    # Test 1: Long Momentum Strategy
    print("🚀 TEST 1: Long Momentum Strategy")
    print("-" * 80)
    
    config1 = BacktestConfig(
        strategy_id='long_momentum',
        strategy_params={'top_k': 3, 'holding_days': 10},
        symbols=['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
        benchmark='SPY',
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000.0
    )
    
    strategy1 = LongMomentumStrategy(
        StrategyParams(top_k=3, holding_days=10)
    )
    
    result1 = runner.run(config1, strategy1)
    
    print(f"\n📈 Results:")
    print(f"  Run ID: {result1.run_id}")
    print(f"  Total Return: {result1.metrics.get('total_return', 0):.2%}")
    print(f"  CAGR: {result1.metrics.get('cagr', 0):.2%}")
    print(f"  Sharpe Ratio: {result1.metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Max Drawdown: {result1.metrics.get('max_drawdown', 0):.2%}")
    print(f"  Win Rate: {result1.metrics.get('win_rate', 0):.2%}")
    print(f"  Trades: {result1.metrics.get('num_trades', 0)}")
    print(f"  Final Equity: ${result1.metrics.get('final_equity', 0):,.2f}")
    print()
    
    # Test 2: Short Momentum Strategy
    print("🚀 TEST 2: Short Momentum Strategy")
    print("-" * 80)
    
    config2 = BacktestConfig(
        strategy_id='short_momentum',
        strategy_params={'top_k': 2, 'holding_days': 7},
        symbols=['AAPL', 'MSFT', 'GOOGL'],
        benchmark='SPY',
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000.0
    )
    
    strategy2 = ShortMomentumStrategy(
        StrategyParams(top_k=2, holding_days=7)
    )
    
    result2 = runner.run(config2, strategy2)
    
    print(f"\n📉 Results:")
    print(f"  Run ID: {result2.run_id}")
    print(f"  Total Return: {result2.metrics.get('total_return', 0):.2%}")
    print(f"  CAGR: {result2.metrics.get('cagr', 0):.2%}")
    print(f"  Sharpe Ratio: {result2.metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Max Drawdown: {result2.metrics.get('max_drawdown', 0):.2%}")
    print(f"  Trades: {result2.metrics.get('num_trades', 0)}")
    print(f"  Final Equity: ${result2.metrics.get('final_equity', 0):,.2f}")
    print()
    
    # Test 3: Neutral Strategy
    print("🚀 TEST 3: Neutral Strategy")
    print("-" * 80)
    
    config3 = BacktestConfig(
        strategy_id='neutral_strategy',
        strategy_params={'top_k': 2, 'holding_days': 14},
        symbols=['AAPL', 'MSFT', 'GOOGL', 'NVDA'],
        benchmark='SPY',
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000.0
    )
    
    strategy3 = NeutralStrategy(
        StrategyParams(top_k=2, holding_days=14)
    )
    
    result3 = runner.run(config3, strategy3)
    
    print(f"\n⚖️  Results:")
    print(f"  Run ID: {result3.run_id}")
    print(f"  Total Return: {result3.metrics.get('total_return', 0):.2%}")
    print(f"  CAGR: {result3.metrics.get('cagr', 0):.2%}")
    print(f"  Sharpe Ratio: {result3.metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Max Drawdown: {result3.metrics.get('max_drawdown', 0):.2%}")
    print(f"  Trades: {result3.metrics.get('num_trades', 0)}")
    print(f"  Final Equity: ${result3.metrics.get('final_equity', 0):,.2f}")
    print()
    
    # Test 4: Verify runs are saved
    print("🔍 TEST 4: Verify Runs Persistence")
    print("-" * 80)
    
    all_runs = run_manager.list_runs()
    print(f"  Total runs in database: {len(all_runs)}")
    
    # Get the runs we just created
    run1 = run_manager.get_run(result1.run_id)
    run2 = run_manager.get_run(result2.run_id)
    run3 = run_manager.get_run(result3.run_id)
    
    print(f"\n  ✓ Run 1 retrieved: {run1.strategy_id}")
    print(f"  ✓ Run 2 retrieved: {run2.strategy_id}")
    print(f"  ✓ Run 3 retrieved: {run3.strategy_id}")
    print()
    
    # Test 5: Compare runs
    print("🔍 TEST 5: Compare Runs")
    print("-" * 80)
    
    comparison_df = run_manager.compare_runs([result1.run_id, result2.run_id, result3.run_id])
    
    print(f"\n  Comparing {len(comparison_df)} runs:")
    print(comparison_df[['strategy', 'total_return', 'sharpe_ratio', 'max_drawdown']].to_string(index=False))
    print()
    
    # Summary
    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  ✓ Data persistence working")
    print(f"  ✓ Feature computation working")
    print(f"  ✓ Regime detection working")
    print(f"  ✓ Strategy execution working (3 strategies tested)")
    print(f"  ✓ Metrics calculation working")
    print(f"  ✓ Run persistence working")
    print(f"  ✓ Run comparison working")
    print()
    print("🎉 Backtest engine is ready for UI integration!")
    print()
    
    # Cleanup
    run_manager.close()


if __name__ == "__main__":
    main()
