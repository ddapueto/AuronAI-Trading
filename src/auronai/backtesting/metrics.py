"""
Performance metrics calculation for backtesting.

This module provides comprehensive performance metrics including returns,
risk-adjusted metrics, drawdown analysis, and trade statistics.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from auronai.utils.logger import get_logger

logger = get_logger(__name__)


class MetricsCalculator:
    """
    Calculate comprehensive backtest performance metrics.
    
    **Validates: Requirements FR-11**
    """
    
    @staticmethod
    def calculate_all_metrics(
        equity_curve: pd.DataFrame,
        trades: List[Dict],
        initial_capital: float,
        regime_history: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        Calculate all performance metrics.
        
        Args:
            equity_curve: DataFrame with 'date' and 'equity' columns
            trades: List of trade dictionaries
            initial_capital: Starting capital
            regime_history: Optional DataFrame with regime breakdown
        
        Returns:
            Dictionary with all metrics
        """
        if equity_curve.empty:
            return {}
        
        metrics = {}
        
        # Convert equity to series
        equity_series = pd.Series(
            equity_curve['equity'].values,
            index=pd.to_datetime(equity_curve['date'])
        )
        
        # Return metrics
        metrics.update(
            MetricsCalculator._calculate_return_metrics(
                equity_series,
                initial_capital
            )
        )
        
        # Risk metrics
        metrics.update(
            MetricsCalculator._calculate_risk_metrics(
                equity_series,
                initial_capital
            )
        )
        
        # Trade statistics
        metrics.update(
            MetricsCalculator._calculate_trade_metrics(trades)
        )
        
        # Exposure
        metrics['exposure'] = MetricsCalculator._calculate_exposure(
            equity_series,
            initial_capital
        )
        
        # Regime breakdown (if available)
        if regime_history is not None:
            metrics.update(
                MetricsCalculator._calculate_regime_metrics(
                    equity_series,
                    regime_history
                )
            )
        
        return metrics
    
    @staticmethod
    def _calculate_return_metrics(
        equity_series: pd.Series,
        initial_capital: float
    ) -> Dict[str, float]:
        """Calculate return-based metrics."""
        final_equity = equity_series.iloc[-1]
        
        # Total return
        total_return = (final_equity / initial_capital) - 1.0
        
        # CAGR (Compound Annual Growth Rate)
        days = (equity_series.index[-1] - equity_series.index[0]).days
        years = days / 365.25
        
        if years > 0:
            cagr = (final_equity / initial_capital) ** (1 / years) - 1.0
        else:
            cagr = 0.0
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'final_equity': float(final_equity)
        }
    
    @staticmethod
    def _calculate_risk_metrics(
        equity_series: pd.Series,
        initial_capital: float
    ) -> Dict[str, float]:
        """Calculate risk-adjusted metrics."""
        # Daily returns
        returns = equity_series.pct_change().dropna()
        
        # Sharpe Ratio (annualized, assuming risk-free rate = 0)
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Sortino Ratio (only penalizes downside volatility)
        if len(returns) > 1:
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0 and downside_returns.std() > 0:
                sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(252)
            else:
                sortino_ratio = 0.0
        else:
            sortino_ratio = 0.0
        
        # Max Drawdown
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # Calmar Ratio (CAGR / abs(Max Drawdown))
        days = (equity_series.index[-1] - equity_series.index[0]).days
        years = days / 365.25
        
        if years > 0:
            cagr = (equity_series.iloc[-1] / initial_capital) ** (1 / years) - 1.0
            calmar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else 0.0
        else:
            calmar_ratio = 0.0
        
        # Recovery Factor (Total Return / abs(Max Drawdown))
        total_return = (equity_series.iloc[-1] / initial_capital) - 1.0
        recovery_factor = total_return / abs(max_drawdown) if max_drawdown != 0 else 0.0
        
        # Average Drawdown Duration (in days)
        in_drawdown = drawdown < 0
        durations = []
        current_duration = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
            elif current_duration > 0:
                durations.append(current_duration)
                current_duration = 0
        
        if current_duration > 0:
            durations.append(current_duration)
        
        avg_dd_duration = np.mean(durations) if durations else 0.0
        max_dd_duration = max(durations) if durations else 0.0
        
        # Ulcer Index (measures pain of drawdowns)
        drawdown_pct = drawdown * 100  # Convert to percentage
        ulcer_index = np.sqrt((drawdown_pct ** 2).mean())
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'recovery_factor': recovery_factor,
            'avg_dd_duration': avg_dd_duration,
            'max_dd_duration': max_dd_duration,
            'ulcer_index': ulcer_index,
            'volatility': volatility
        }
    
    @staticmethod
    def _calculate_trade_metrics(trades: List[Dict]) -> Dict[str, float]:
        """Calculate trade statistics."""
        if not trades:
            return {
                'num_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'expectancy': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }
        
        # Filter closed trades (with pnl_dollar)
        closed_trades = [
            t for t in trades
            if t.get('pnl_dollar') is not None
        ]
        
        if not closed_trades:
            return {
                'num_trades': len(trades),
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'expectancy': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }
        
        pnls = [t['pnl_dollar'] for t in closed_trades]
        
        # Winning and losing trades
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        # Win rate
        win_rate = len(wins) / len(closed_trades) if closed_trades else 0.0
        
        # Profit factor
        total_wins = sum(wins) if wins else 0.0
        total_losses = abs(sum(losses)) if losses else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        # Expectancy
        expectancy = sum(pnls) / len(pnls) if pnls else 0.0
        
        # Average win/loss
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        
        # Largest win/loss
        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0
        
        # Consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for pnl in pnls:
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        return {
            'num_trades': len(closed_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses
        }
    
    @staticmethod
    def _calculate_exposure(
        equity_series: pd.Series,
        initial_capital: float
    ) -> float:
        """
        Calculate market exposure (% of time invested).
        
        Simplified: assumes always invested for MVP.
        """
        return 1.0
    
    @staticmethod
    def _calculate_regime_metrics(
        equity_series: pd.Series,
        regime_history: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate performance breakdown by regime.
        
        Args:
            equity_series: Equity over time
            regime_history: DataFrame with 'date' and 'regime' columns
        
        Returns:
            Dictionary with regime-specific metrics
        """
        # Align regime history with equity
        regime_series = pd.Series(
            regime_history['regime'].values,
            index=pd.to_datetime(regime_history['date'])
        )
        
        # Calculate returns by regime
        returns = equity_series.pct_change().dropna()
        
        metrics = {}
        
        for regime in ['bull', 'bear', 'neutral']:
            regime_mask = regime_series == regime
            regime_returns = returns[regime_mask]
            
            if len(regime_returns) > 0:
                total_return = (1 + regime_returns).prod() - 1
                metrics[f'{regime}_return'] = total_return
                metrics[f'{regime}_days'] = len(regime_returns)
            else:
                metrics[f'{regime}_return'] = 0.0
                metrics[f'{regime}_days'] = 0
        
        return metrics
