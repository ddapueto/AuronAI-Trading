"""
Tests for BacktestRunner.

Tests backtest orchestration and execution.
"""

import tempfile
from datetime import datetime

import pandas as pd
import pytest

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
    StrategyParams,
    RegimeEngine
)


class TestBacktestRunnerBasic:
    """Basic tests for BacktestRunner."""
    
    def test_backtest_runner_instantiation(self):
        """Should create BacktestRunner instance."""
        runner = BacktestRunner()
        
        assert runner.parquet_cache is not None
        assert runner.feature_store is not None
        assert runner.regime_engine is not None
        assert runner.run_manager is not None
    
    @pytest.mark.slow
    def test_run_simple_backtest_with_demo_data(self):
        """Should run a simple backtest with demo data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup components
            cache = ParquetCache(cache_dir=f"{tmpdir}/cache")
            feature_store = FeatureStore(cache_dir=f"{tmpdir}/cache")
            regime_engine = RegimeEngine(benchmark='QQQ')
            run_manager = RunManager(db_path=f"{tmpdir}/runs.db")
            
            runner = BacktestRunner(
                parquet_cache=cache,
                feature_store=feature_store,
                regime_engine=regime_engine,
                run_manager=run_manager
            )
            
            # Generate demo data with specific date range
            simulator = DemoSimulator(seed=42)
            symbols = ['AAPL', 'MSFT', 'QQQ']
            
            start_date = datetime(2023, 1, 1)
            end_date = datetime(2023, 3, 31)
            
            for symbol in symbols:
                if symbol == 'QQQ':
                    data = simulator.generate_price_data(
                        symbol=symbol,
                        days=90,
                        initial_price=300.0,
                        volatility=0.015,
                        drift=0.0
                    )
                else:
                    data = simulator.generate_trending_market(
                        symbol=symbol,
                        days=90,
                        initial_price=150.0,
                        direction='up',
                        strength=0.001,
                        volatility=0.02
                    )
                
                # Adjust index to match requested date range
                data.index = pd.date_range(start=start_date, periods=len(data), freq='D')
                cache.save_data(symbol, data)
            
            # Create config
            config = BacktestConfig(
                strategy_id='long_momentum',
                strategy_params={'top_k': 2, 'holding_days': 10},
                symbols=['AAPL', 'MSFT'],
                benchmark='QQQ',
                start_date=start_date,
                end_date=end_date,
                initial_capital=100000.0
            )
            
            # Create strategy
            strategy = LongMomentumStrategy(
                StrategyParams(top_k=2, holding_days=10)
            )
            
            # Run backtest
            result = runner.run(config, strategy)
            
            # Verify result
            assert result.run_id is not None
            assert len(result.run_id) == 36  # UUID
            assert result.config == config
            assert 'total_return' in result.metrics
            assert 'max_drawdown' in result.metrics
            assert len(result.equity_curve) > 0
            assert result.equity_curve['equity'].iloc[0] == 100000.0
            
            # Verify run was saved
            saved_run = run_manager.get_run(result.run_id)
            assert saved_run is not None
            assert saved_run.strategy_id == 'long_momentum'
            
            run_manager.close()
    
    def test_backtest_config_validation(self):
        """Should validate backtest configuration."""
        # Empty symbols
        with pytest.raises(ValueError, match="symbols list cannot be empty"):
            BacktestConfig(
                strategy_id='test',
                strategy_params={},
                symbols=[],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31)
            )
        
        # Invalid date range
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            BacktestConfig(
                strategy_id='test',
                strategy_params={},
                symbols=['AAPL'],
                benchmark='QQQ',
                start_date=datetime(2023, 12, 31),
                end_date=datetime(2023, 1, 1)
            )
        
        # Invalid capital
        with pytest.raises(ValueError, match="initial_capital must be positive"):
            BacktestConfig(
                strategy_id='test',
                strategy_params={},
                symbols=['AAPL'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=-1000.0
            )
    
    def test_backtest_config_serialization(self):
        """Should serialize and deserialize config."""
        config = BacktestConfig(
            strategy_id='long_momentum',
            strategy_params={'top_k': 3},
            symbols=['AAPL', 'MSFT'],
            benchmark='QQQ',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0
        )
        
        # Serialize
        config_dict = config.to_dict()
        
        assert config_dict['strategy_id'] == 'long_momentum'
        assert config_dict['symbols'] == ['AAPL', 'MSFT']
        assert isinstance(config_dict['start_date'], str)
        
        # Deserialize
        config2 = BacktestConfig.from_dict(config_dict)
        
        assert config2.strategy_id == config.strategy_id
        assert config2.symbols == config.symbols
        assert config2.start_date == config.start_date
