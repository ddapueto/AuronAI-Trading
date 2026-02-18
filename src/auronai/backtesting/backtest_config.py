"""
Backtest configuration and result dataclasses.

This module defines the data structures for configuring and storing
backtest results.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional

import pandas as pd


@dataclass
class BacktestConfig:
    """
    Configuration for a backtest run.
    
    Attributes:
        strategy_id: Strategy identifier (e.g., "long_momentum")
        strategy_params: Strategy parameters dict
        symbols: List of symbols to trade
        benchmark: Benchmark symbol for regime detection (e.g., "QQQ")
        start_date: Backtest start date
        end_date: Backtest end date
        initial_capital: Starting capital in USD
        commission_rate: Commission per trade as decimal (e.g., 0.001 = 0.1%)
        slippage_rate: Slippage as decimal (e.g., 0.0005 = 0.05%)
    
    **Validates: Requirements FR-12**
    """
    
    strategy_id: str
    strategy_params: Dict[str, Any]
    symbols: List[str]
    benchmark: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000.0
    commission_rate: float = 0.0000  # 0% - Use free broker (Robinhood, Webull, Libertex)
    slippage_rate: float = 0.0003    # 0.03% - Realistic for liquid stocks
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not self.symbols:
            raise ValueError("symbols list cannot be empty")
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        if self.commission_rate < 0:
            raise ValueError("commission_rate cannot be negative")
        if self.slippage_rate < 0:
            raise ValueError("slippage_rate cannot be negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary.
        
        Returns:
            Dictionary representation with dates as ISO strings
        """
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestConfig':
        """
        Create config from dictionary.
        
        Args:
            data: Dictionary with config data
        
        Returns:
            BacktestConfig instance
        """
        data = data.copy()
        data['start_date'] = datetime.fromisoformat(data['start_date'])
        data['end_date'] = datetime.fromisoformat(data['end_date'])
        return cls(**data)


@dataclass
class Trade:
    """
    Individual trade record.
    
    Attributes:
        symbol: Stock symbol
        entry_date: Entry date
        exit_date: Exit date (None if still open)
        entry_price: Entry price per share
        exit_price: Exit price per share (None if still open)
        shares: Number of shares
        direction: 'long' or 'short'
        pnl_dollar: Profit/loss in dollars (None if still open)
        pnl_percent: Profit/loss as percentage (None if still open)
        reason: Exit reason (e.g., 'take_profit', 'time_exit', 'stop_loss')
    """
    
    symbol: str
    entry_date: str
    exit_date: Optional[str]
    entry_price: float
    exit_price: Optional[float]
    shares: float
    direction: str
    pnl_dollar: Optional[float]
    pnl_percent: Optional[float]
    reason: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return asdict(self)


@dataclass
class BacktestResult:
    """
    Results from a backtest run.
    
    Attributes:
        run_id: Unique run identifier (UUID)
        config: Backtest configuration
        metrics: Performance metrics dict
        trades: List of trade records
        equity_curve: DataFrame with date and equity columns
        regime_history: DataFrame with date and regime columns (optional)
    
    **Validates: Requirements FR-12**
    """
    
    run_id: str
    config: BacktestConfig
    metrics: Dict[str, float]
    trades: List[Dict[str, Any]]
    equity_curve: pd.DataFrame
    regime_history: Optional[pd.DataFrame] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.
        
        Returns:
            Dictionary representation (without large DataFrames)
        """
        return {
            'run_id': self.run_id,
            'config': self.config.to_dict(),
            'metrics': self.metrics,
            'num_trades': len(self.trades),
            'start_equity': float(self.equity_curve['equity'].iloc[0]) if len(self.equity_curve) > 0 else 0.0,
            'end_equity': float(self.equity_curve['equity'].iloc[-1]) if len(self.equity_curve) > 0 else 0.0
        }
    
    def get_trades_df(self) -> pd.DataFrame:
        """
        Get trades as DataFrame.
        
        Returns:
            DataFrame with trade records
        """
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame(self.trades)
    
    def get_winning_trades(self) -> pd.DataFrame:
        """
        Get only winning trades.
        
        Returns:
            DataFrame with trades where pnl_dollar > 0
        """
        trades_df = self.get_trades_df()
        if trades_df.empty:
            return trades_df
        return trades_df[trades_df['pnl_dollar'] > 0]
    
    def get_losing_trades(self) -> pd.DataFrame:
        """
        Get only losing trades.
        
        Returns:
            DataFrame with trades where pnl_dollar < 0
        """
        trades_df = self.get_trades_df()
        if trades_df.empty:
            return trades_df
        return trades_df[trades_df['pnl_dollar'] < 0]
    
    def summary(self) -> str:
        """
        Get human-readable summary.
        
        Returns:
            Multi-line string with key metrics
        """
        lines = [
            f"Backtest Results (Run ID: {self.run_id})",
            f"Strategy: {self.config.strategy_id}",
            f"Period: {self.config.start_date.date()} to {self.config.end_date.date()}",
            f"Symbols: {len(self.config.symbols)}",
            "",
            "Performance Metrics:",
        ]
        
        for metric, value in sorted(self.metrics.items()):
            if 'return' in metric.lower() or 'drawdown' in metric.lower():
                lines.append(f"  {metric}: {value:.2%}")
            else:
                lines.append(f"  {metric}: {value:.4f}")
        
        lines.extend([
            "",
            f"Total Trades: {len(self.trades)}",
            f"Winning Trades: {len(self.get_winning_trades())}",
            f"Losing Trades: {len(self.get_losing_trades())}",
        ])
        
        return "\n".join(lines)
