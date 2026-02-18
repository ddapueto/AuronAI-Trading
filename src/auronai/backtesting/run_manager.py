"""
Run manager for backtest metadata persistence.

This module manages backtest runs using SQLite, storing run configurations,
metrics, trades, and equity curves for reproducibility and comparison.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from auronai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestRun:
    """
    Metadata for a backtest run.
    
    Attributes:
        run_id: Unique identifier (UUID)
        strategy_id: Strategy identifier
        strategy_params: Strategy parameters as dict
        symbols: List of symbols traded
        benchmark: Benchmark symbol for regime detection
        start_date: Backtest start date
        end_date: Backtest end date
        initial_capital: Starting capital
        data_version: SHA256 hash of data used
        code_version: Git commit hash
        created_at: Timestamp of run creation
        metrics: Performance metrics dict
    """
    
    run_id: str
    strategy_id: str
    strategy_params: Dict[str, Any]
    symbols: List[str]
    benchmark: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    data_version: str
    code_version: str
    created_at: datetime
    metrics: Dict[str, float]


class RunManager:
    """
    Manages backtest runs using SQLite.
    
    Database Schema:
    - runs: Run metadata and configuration
    - metrics: Performance metrics per run
    - trades: Individual trades per run
    - equity_curve: Daily equity values per run
    
    **Validates: Requirements FR-12, FR-13, FR-14**
    """
    
    def __init__(self, db_path: str = "data/runs.db"):
        """
        Initialize run manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        self._create_tables()
        
        logger.info(f"RunManager initialized with database: {self.db_path}")
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                strategy_params TEXT NOT NULL,
                symbols TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                data_version TEXT NOT NULL,
                code_version TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                run_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                PRIMARY KEY (run_id, metric_name),
                FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            )
        """)
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                run_id TEXT NOT NULL,
                trade_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                exit_date TEXT,
                entry_price REAL NOT NULL,
                exit_price REAL,
                shares REAL NOT NULL,
                pnl_dollar REAL,
                pnl_percent REAL,
                reason TEXT,
                PRIMARY KEY (run_id, trade_id),
                FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            )
        """)
        
        # Equity curve table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equity_curve (
                run_id TEXT NOT NULL,
                date TEXT NOT NULL,
                equity REAL NOT NULL,
                PRIMARY KEY (run_id, date),
                FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_strategy 
            ON runs(strategy_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_created 
            ON runs(created_at DESC)
        """)
        
        self.conn.commit()
        logger.debug("Database tables created/verified")
    
    def save_run(
        self,
        strategy_id: str,
        strategy_params: Dict[str, Any],
        symbols: List[str],
        benchmark: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        data_version: str,
        code_version: str,
        metrics: Dict[str, float],
        trades: List[Dict[str, Any]],
        equity_curve: pd.DataFrame
    ) -> str:
        """
        Save backtest run to database.
        
        Args:
            strategy_id: Strategy identifier
            strategy_params: Strategy parameters
            symbols: List of symbols traded
            benchmark: Benchmark symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            data_version: SHA256 hash of data
            code_version: Git commit hash
            metrics: Performance metrics dict
            trades: List of trade dicts
            equity_curve: DataFrame with date and equity columns
        
        Returns:
            run_id (UUID string)
        """
        run_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        cursor = self.conn.cursor()
        
        try:
            # Insert run metadata
            cursor.execute("""
                INSERT INTO runs (
                    run_id, strategy_id, strategy_params, symbols, benchmark,
                    start_date, end_date, initial_capital, data_version,
                    code_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                strategy_id,
                json.dumps(strategy_params),
                json.dumps(symbols),
                benchmark,
                start_date.isoformat(),
                end_date.isoformat(),
                initial_capital,
                data_version,
                code_version,
                created_at.isoformat()
            ))
            
            # Insert metrics
            for metric_name, metric_value in metrics.items():
                cursor.execute("""
                    INSERT INTO metrics (run_id, metric_name, metric_value)
                    VALUES (?, ?, ?)
                """, (run_id, metric_name, float(metric_value)))
            
            # Insert trades
            for i, trade in enumerate(trades):
                cursor.execute("""
                    INSERT INTO trades (
                        run_id, trade_id, symbol, entry_date, exit_date,
                        entry_price, exit_price, shares, pnl_dollar,
                        pnl_percent, reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    i,
                    trade['symbol'],
                    trade['entry_date'],
                    trade.get('exit_date'),
                    trade['entry_price'],
                    trade.get('exit_price'),
                    trade['shares'],
                    trade.get('pnl_dollar'),
                    trade.get('pnl_percent'),
                    trade.get('reason')
                ))
            
            # Insert equity curve
            for _, row in equity_curve.iterrows():
                cursor.execute("""
                    INSERT INTO equity_curve (run_id, date, equity)
                    VALUES (?, ?, ?)
                """, (run_id, row['date'], row['equity']))
            
            self.conn.commit()
            
            logger.info(
                f"Saved run {run_id}: {strategy_id}, "
                f"{len(trades)} trades, {len(metrics)} metrics"
            )
            
            return run_id
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error saving run: {e}")
            raise
    
    def get_run(self, run_id: str) -> Optional[BacktestRun]:
        """
        Load run metadata by ID.
        
        Args:
            run_id: Run UUID
        
        Returns:
            BacktestRun object or None if not found
        """
        cursor = self.conn.cursor()
        
        # Get run metadata
        cursor.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Get metrics
        cursor.execute(
            "SELECT metric_name, metric_value FROM metrics WHERE run_id = ?",
            (run_id,)
        )
        metrics = {row['metric_name']: row['metric_value'] for row in cursor.fetchall()}
        
        return BacktestRun(
            run_id=row['run_id'],
            strategy_id=row['strategy_id'],
            strategy_params=json.loads(row['strategy_params']),
            symbols=json.loads(row['symbols']),
            benchmark=row['benchmark'],
            start_date=datetime.fromisoformat(row['start_date']),
            end_date=datetime.fromisoformat(row['end_date']),
            initial_capital=row['initial_capital'],
            data_version=row['data_version'],
            code_version=row['code_version'],
            created_at=datetime.fromisoformat(row['created_at']),
            metrics=metrics
        )
    
    def list_runs(
        self,
        strategy_id: Optional[str] = None,
        limit: int = 100
    ) -> List[BacktestRun]:
        """
        List recent runs, optionally filtered by strategy.
        
        Args:
            strategy_id: Filter by strategy (None = all strategies)
            limit: Maximum number of runs to return
        
        Returns:
            List of BacktestRun objects, sorted by created_at DESC
        """
        cursor = self.conn.cursor()
        
        if strategy_id:
            cursor.execute("""
                SELECT run_id FROM runs
                WHERE strategy_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (strategy_id, limit))
        else:
            cursor.execute("""
                SELECT run_id FROM runs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        run_ids = [row['run_id'] for row in cursor.fetchall()]
        
        return [self.get_run(run_id) for run_id in run_ids if self.get_run(run_id)]
    
    def compare_runs(self, run_ids: List[str]) -> pd.DataFrame:
        """
        Compare metrics across multiple runs.
        
        Args:
            run_ids: List of run UUIDs to compare
        
        Returns:
            DataFrame with runs as rows, metrics as columns
        """
        runs_data = []
        
        for run_id in run_ids:
            run = self.get_run(run_id)
            if run:
                row_data = {
                    'run_id': run.run_id,
                    'strategy': run.strategy_id,
                    'created_at': run.created_at,
                    **run.metrics
                }
                runs_data.append(row_data)
        
        if not runs_data:
            return pd.DataFrame()
        
        return pd.DataFrame(runs_data)
    
    def get_trades(self, run_id: str) -> pd.DataFrame:
        """
        Get all trades for a run.
        
        Args:
            run_id: Run UUID
        
        Returns:
            DataFrame with trade details
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trades
            WHERE run_id = ?
            ORDER BY trade_id
        """, (run_id,))
        
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        return pd.DataFrame([dict(row) for row in rows])
    
    def get_equity_curve(self, run_id: str) -> pd.DataFrame:
        """
        Get equity curve for a run.
        
        Args:
            run_id: Run UUID
        
        Returns:
            DataFrame with date and equity columns
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT date, equity FROM equity_curve
            WHERE run_id = ?
            ORDER BY date
        """, (run_id,))
        
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame([dict(row) for row in rows])
        df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def delete_run(self, run_id: str) -> None:
        """
        Delete a run and all associated data.
        
        Args:
            run_id: Run UUID to delete
        """
        cursor = self.conn.cursor()
        
        cursor.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
        
        self.conn.commit()
        
        logger.info(f"Deleted run {run_id}")
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
        logger.debug("Database connection closed")
