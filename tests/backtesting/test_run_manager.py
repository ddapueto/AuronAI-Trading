"""
Tests for RunManager.

Tests run persistence, retrieval, and comparison functionality.
"""

import tempfile
from datetime import datetime

import pandas as pd
import pytest

from auronai.backtesting import RunManager, BacktestRun


class TestRunManagerBasic:
    """Basic tests for RunManager."""
    
    def test_run_manager_instantiation(self):
        """Should create RunManager and initialize database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_runs.db"
            manager = RunManager(db_path=db_path)
            
            assert manager.db_path.exists()
            manager.close()
    
    def test_save_and_retrieve_run(self):
        """Should save and retrieve a run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_runs.db"
            manager = RunManager(db_path=db_path)
            
            # Save a run
            run_id = manager.save_run(
                strategy_id="long_momentum",
                strategy_params={'top_k': 3, 'holding_days': 10},
                symbols=['AAPL', 'MSFT', 'GOOGL'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000.0,
                data_version="abc123",
                code_version="def456",
                metrics={
                    'total_return': 0.15,
                    'sharpe_ratio': 1.5,
                    'max_drawdown': -0.10
                },
                trades=[
                    {
                        'symbol': 'AAPL',
                        'entry_date': '2023-01-15',
                        'exit_date': '2023-01-25',
                        'entry_price': 150.0,
                        'exit_price': 157.5,
                        'shares': 100,
                        'pnl_dollar': 750.0,
                        'pnl_percent': 0.05,
                        'reason': 'take_profit'
                    }
                ],
                equity_curve=pd.DataFrame({
                    'date': ['2023-01-01', '2023-01-02'],
                    'equity': [100000.0, 100500.0]
                })
            )
            
            assert run_id is not None
            assert len(run_id) == 36  # UUID length
            
            # Retrieve the run
            run = manager.get_run(run_id)
            
            assert run is not None
            assert run.run_id == run_id
            assert run.strategy_id == "long_momentum"
            assert run.symbols == ['AAPL', 'MSFT', 'GOOGL']
            assert run.metrics['total_return'] == 0.15
            assert run.metrics['sharpe_ratio'] == 1.5
            
            manager.close()
    
    def test_list_runs(self):
        """Should list runs with optional filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_runs.db"
            manager = RunManager(db_path=db_path)
            
            # Save multiple runs
            run_id1 = manager.save_run(
                strategy_id="long_momentum",
                strategy_params={'top_k': 3},
                symbols=['AAPL'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000.0,
                data_version="v1",
                code_version="c1",
                metrics={'total_return': 0.10},
                trades=[],
                equity_curve=pd.DataFrame({'date': ['2023-01-01'], 'equity': [100000.0]})
            )
            
            run_id2 = manager.save_run(
                strategy_id="short_momentum",
                strategy_params={'top_k': 2},
                symbols=['MSFT'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000.0,
                data_version="v1",
                code_version="c1",
                metrics={'total_return': 0.05},
                trades=[],
                equity_curve=pd.DataFrame({'date': ['2023-01-01'], 'equity': [100000.0]})
            )
            
            # List all runs
            all_runs = manager.list_runs()
            assert len(all_runs) == 2
            
            # List filtered by strategy
            long_runs = manager.list_runs(strategy_id="long_momentum")
            assert len(long_runs) == 1
            assert long_runs[0].strategy_id == "long_momentum"
            
            manager.close()
    
    def test_compare_runs(self):
        """Should compare metrics across runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_runs.db"
            manager = RunManager(db_path=db_path)
            
            # Save two runs
            run_id1 = manager.save_run(
                strategy_id="long_momentum",
                strategy_params={'top_k': 3},
                symbols=['AAPL'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000.0,
                data_version="v1",
                code_version="c1",
                metrics={'total_return': 0.15, 'sharpe_ratio': 1.5},
                trades=[],
                equity_curve=pd.DataFrame({'date': ['2023-01-01'], 'equity': [100000.0]})
            )
            
            run_id2 = manager.save_run(
                strategy_id="short_momentum",
                strategy_params={'top_k': 2},
                symbols=['MSFT'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000.0,
                data_version="v1",
                code_version="c1",
                metrics={'total_return': 0.10, 'sharpe_ratio': 1.2},
                trades=[],
                equity_curve=pd.DataFrame({'date': ['2023-01-01'], 'equity': [100000.0]})
            )
            
            # Compare runs
            comparison = manager.compare_runs([run_id1, run_id2])
            
            assert len(comparison) == 2
            assert 'total_return' in comparison.columns
            assert 'sharpe_ratio' in comparison.columns
            assert comparison['total_return'].iloc[0] == 0.15
            assert comparison['total_return'].iloc[1] == 0.10
            
            manager.close()
    
    def test_get_trades(self):
        """Should retrieve trades for a run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_runs.db"
            manager = RunManager(db_path=db_path)
            
            run_id = manager.save_run(
                strategy_id="long_momentum",
                strategy_params={'top_k': 3},
                symbols=['AAPL'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000.0,
                data_version="v1",
                code_version="c1",
                metrics={'total_return': 0.10},
                trades=[
                    {
                        'symbol': 'AAPL',
                        'entry_date': '2023-01-15',
                        'exit_date': '2023-01-25',
                        'entry_price': 150.0,
                        'exit_price': 157.5,
                        'shares': 100,
                        'pnl_dollar': 750.0,
                        'pnl_percent': 0.05,
                        'reason': 'take_profit'
                    },
                    {
                        'symbol': 'MSFT',
                        'entry_date': '2023-02-01',
                        'exit_date': '2023-02-10',
                        'entry_price': 250.0,
                        'exit_price': 245.0,
                        'shares': 50,
                        'pnl_dollar': -250.0,
                        'pnl_percent': -0.02,
                        'reason': 'stop_loss'
                    }
                ],
                equity_curve=pd.DataFrame({'date': ['2023-01-01'], 'equity': [100000.0]})
            )
            
            trades = manager.get_trades(run_id)
            
            assert len(trades) == 2
            assert trades['symbol'].iloc[0] == 'AAPL'
            assert trades['pnl_dollar'].iloc[0] == 750.0
            assert trades['symbol'].iloc[1] == 'MSFT'
            assert trades['pnl_dollar'].iloc[1] == -250.0
            
            manager.close()
    
    def test_get_equity_curve(self):
        """Should retrieve equity curve for a run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_runs.db"
            manager = RunManager(db_path=db_path)
            
            run_id = manager.save_run(
                strategy_id="long_momentum",
                strategy_params={'top_k': 3},
                symbols=['AAPL'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000.0,
                data_version="v1",
                code_version="c1",
                metrics={'total_return': 0.10},
                trades=[],
                equity_curve=pd.DataFrame({
                    'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
                    'equity': [100000.0, 100500.0, 101000.0]
                })
            )
            
            equity_curve = manager.get_equity_curve(run_id)
            
            assert len(equity_curve) == 3
            assert equity_curve['equity'].iloc[0] == 100000.0
            assert equity_curve['equity'].iloc[2] == 101000.0
            
            manager.close()
    
    def test_delete_run(self):
        """Should delete a run and all associated data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_runs.db"
            manager = RunManager(db_path=db_path)
            
            run_id = manager.save_run(
                strategy_id="long_momentum",
                strategy_params={'top_k': 3},
                symbols=['AAPL'],
                benchmark='QQQ',
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000.0,
                data_version="v1",
                code_version="c1",
                metrics={'total_return': 0.10},
                trades=[],
                equity_curve=pd.DataFrame({'date': ['2023-01-01'], 'equity': [100000.0]})
            )
            
            # Verify run exists
            assert manager.get_run(run_id) is not None
            
            # Delete run
            manager.delete_run(run_id)
            
            # Verify run is deleted
            assert manager.get_run(run_id) is None
            
            manager.close()
