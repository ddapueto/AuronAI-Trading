"""Swing Strategy LONG/SHORT V1 - Regime-Based Directional Trading.

Evolution from Multi-Asset V1:
- Adds SHORT capability for bear markets
- Regime detection using QQQ (EMA200, slope, ADX)
- Long in bull markets (current baseline)
- Short in bear markets (inverse selection)
- Cash/reduced exposure in neutral markets

Goal: Convert -4.70% (2022 bear) to +5% or more
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np
import logging

from auronai.data.market_data_provider import MarketDataProvider
import pandas_ta as ta

logger = logging.getLogger(__name__)


@dataclass
class SwingTrade:
    """Representa un trade individual (long o short)."""
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry_day: datetime
    entry_price: float
    exit_day: Optional[datetime] = None
    exit_price: Optional[float] = None
    shares: float = 0.0
    tp: float = 0.0
    reason: Optional[str] = None
    pnl_dollar: Optional[float] = None
    pnl_percent: Optional[float] = None


class SwingLongShortV1:
    """
    Estrategia swing LONG/SHORT V1.
    
    Regime-based directional trading:
    - Bull regime → Long top 3 by relative strength
    - Bear regime → Short bottom 3 by relative weakness
    - Neutral regime → Cash or reduced exposure
    """
    
    def __init__(
        self,
        symbols: List[str],
        benchmark: str = 'QQQ',
        initial_capital: float = 1000.0,
        bull_risk_budget: float = 0.20,
        bear_risk_budget: float = 0.15,
        neutral_risk_budget: float = 0.05,
        top_k: int = 3,
        tp_multiplier: float = 1.05,
        max_holding_days: int = 7,
        dd_threshold_pause: float = 0.12,
        dd_threshold_resume: float = 0.08,
        cooldown_days: int = 10
    ):
        """
        Inicializar estrategia swing long/short V1.
        
        Args:
            symbols: Lista de símbolos (acciones + ETFs)
            benchmark: Símbolo de benchmark (default: 'QQQ')
            initial_capital: Capital inicial en USD
            bull_risk_budget: Risk budget en bull market (default: 0.20)
            bear_risk_budget: Risk budget en bear market (default: 0.15)
            neutral_risk_budget: Risk budget en neutral market (default: 0.05)
            top_k: Número de símbolos a seleccionar (default: 3)
            tp_multiplier: Multiplicador para TP (default: 1.05 = 5%)
            max_holding_days: Días máximos de holding (default: 7)
            dd_threshold_pause: DD threshold para pausar (default: 0.12)
            dd_threshold_resume: DD threshold para reanudar (default: 0.08)
            cooldown_days: Días de cooldown (default: 10)
        """
        self.symbols = symbols
        self.benchmark = benchmark
        self.initial_capital = initial_capital
        self.bull_risk_budget = bull_risk_budget
        self.bear_risk_budget = bear_risk_budget
        self.neutral_risk_budget = neutral_risk_budget
        self.top_k = top_k
        self.tp_multiplier = tp_multiplier
        self.max_holding_days = max_holding_days
        self.dd_threshold_pause = dd_threshold_pause
        self.dd_threshold_resume = dd_threshold_resume
        self.cooldown_days = cooldown_days
        
        self.market_data = MarketDataProvider()
        
        # State
        self.equity = initial_capital
        self.peak_equity = initial_capital
        self.open_positions: List[SwingTrade] = []
        self.closed_trades: List[SwingTrade] = []
        self.equity_curve: List[float] = []
        self.dates: List[datetime] = []
        self.cooldown_until: Optional[datetime] = None
        self.paused = False
        
        # Separate ETFs from stocks for neutral regime
        self.etfs = [s for s in symbols if len(s) <= 4 and s.isupper() and s not in [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'AVGO', 'COST'
        ]]
        
        logger.info(
            f"SwingLongShortV1 initialized: {len(symbols)} symbols, "
            f"capital=${initial_capital}, ETFs={len(self.etfs)}"
        )
    
    def _calculate_market_regime(
        self,
        qqq_data: pd.DataFrame,
        current_idx: int
    ) -> str:
        """
        Calcular market regime usando QQQ.
        
        Returns:
            'BULL', 'BEAR', or 'NEUTRAL'
        """
        if current_idx < 200:
            return 'NEUTRAL'
        
        ema200 = ta.ema(qqq_data['Close'], length=200)
        if ema200 is None or len(ema200) <= current_idx:
            return 'NEUTRAL'
        
        current_close = qqq_data['Close'].iloc[current_idx]
        current_ema200 = ema200.iloc[current_idx]
        
        # Check slope
        if current_idx < 220:
            slope = 0
        else:
            slope = ema200.iloc[current_idx] - ema200.iloc[current_idx - 20]
        
        # Calculate ADX
        adx = ta.adx(
            qqq_data['High'],
            qqq_data['Low'],
            qqq_data['Close'],
            length=14
        )
        
        if adx is None or len(adx) <= current_idx:
            adx_value = 0
        else:
            adx_col = [col for col in adx.columns if col.startswith('ADX')][0]
            adx_value = adx[adx_col].iloc[current_idx]
        
        # Determine regime
        if current_close > current_ema200 and slope > 0 and adx_value >= 15:
            regime = 'BULL'
        elif current_close < current_ema200 and slope < 0:
            regime = 'BEAR'
        else:
            regime = 'NEUTRAL'
        
        if current_idx % 20 == 0:
            logger.info(
                f"Regime (day {current_idx}): {regime} "
                f"(close={current_close:.2f}, ema200={current_ema200:.2f}, "
                f"slope={slope:.2f}, adx={adx_value:.2f})"
            )
        
        return regime
    
    def _calculate_risk_budget(
        self,
        regime: str,
        current_date: datetime
    ) -> float:
        """Calcular risk budget dinámico basado en régimen y DD."""
        # Check if paused
        if self.paused:
            dd = (self.peak_equity - self.equity) / self.peak_equity if self.peak_equity > 0 else 0
            if dd < self.dd_threshold_resume:
                self.paused = False
                logger.info(f"RESUMED: DD {dd:.2%} < {self.dd_threshold_resume:.2%}")
            else:
                return 0.0
        
        # Check cooldown
        if self.cooldown_until is not None and current_date < self.cooldown_until:
            return 0.0
        
        # Check DD for pause
        dd = (self.peak_equity - self.equity) / self.peak_equity if self.peak_equity > 0 else 0
        if dd >= self.dd_threshold_pause:
            self.paused = True
            logger.warning(f"PAUSED: DD {dd:.2%} >= {self.dd_threshold_pause:.2%}")
            return 0.0
        
        # Risk budget by regime
        if regime == 'BULL':
            return self.bull_risk_budget
        elif regime == 'BEAR':
            return self.bear_risk_budget
        else:  # NEUTRAL
            return self.neutral_risk_budget
    
    def _calculate_relative_strength(
        self,
        symbol_data: Dict[str, pd.DataFrame],
        qqq_data: pd.DataFrame,
        current_idx: int,
        lookback: int = 20
    ) -> Dict[str, float]:
        """Calcular relative strength score."""
        if current_idx < lookback:
            return {}
        
        rs_scores = {}
        qqq_return = (
            qqq_data['Close'].iloc[current_idx] / qqq_data['Close'].iloc[current_idx - lookback] - 1
        )
        
        for symbol, data in symbol_data.items():
            if len(data) <= current_idx or current_idx < lookback:
                continue
            
            symbol_return = (
                data['Close'].iloc[current_idx] / data['Close'].iloc[current_idx - lookback] - 1
            )
            
            rs_scores[symbol] = symbol_return - qqq_return
        
        return rs_scores
    
    def _select_symbols(
        self,
        rs_scores: Dict[str, float],
        regime: str
    ) -> Tuple[List[str], str]:
        """
        Seleccionar símbolos basado en régimen.
        
        Returns:
            Tuple of (selected_symbols, direction)
            
        BULL: Top 3 strongest, LONG
        BEAR: Bottom 3 weakest, SHORT
        NEUTRAL: Top 1 ETF only, LONG
        """
        if not rs_scores:
            return [], 'LONG'
        
        if regime == 'BULL':
            # Top K strongest for LONG
            sorted_symbols = sorted(rs_scores.items(), key=lambda x: x[1], reverse=True)
            selected = [symbol for symbol, score in sorted_symbols[:self.top_k]]
            return selected, 'LONG'
        
        elif regime == 'BEAR':
            # Bottom K weakest for SHORT
            sorted_symbols = sorted(rs_scores.items(), key=lambda x: x[1], reverse=False)
            selected = [symbol for symbol, score in sorted_symbols[:self.top_k]]
            return selected, 'SHORT'
        
        else:  # NEUTRAL
            # Only 1 ETF, strongest, LONG
            etf_scores = {s: score for s, score in rs_scores.items() if s in self.etfs}
            if not etf_scores:
                return [], 'LONG'
            sorted_etfs = sorted(etf_scores.items(), key=lambda x: x[1], reverse=True)
            return [sorted_etfs[0][0]], 'LONG'
    
    def _open_position(
        self,
        symbol: str,
        direction: str,
        entry_day: datetime,
        entry_price: float,
        allocation: float
    ) -> Optional[SwingTrade]:
        """Abrir nueva posición (long o short)."""
        # Calculate TP
        if direction == 'LONG':
            tp = entry_price * self.tp_multiplier
        else:  # SHORT
            tp = entry_price * (2 - self.tp_multiplier)  # 5% down
        
        # Calculate position size
        position_value = self.equity * allocation
        shares = position_value / entry_price
        
        if shares < 0.01:
            return None
        
        trade = SwingTrade(
            symbol=symbol,
            direction=direction,
            entry_day=entry_day,
            entry_price=entry_price,
            shares=shares,
            tp=tp
        )
        
        self.open_positions.append(trade)
        
        logger.info(
            f"Opened {direction} {symbol}: {shares:.4f} shares @ ${entry_price:.2f}, "
            f"TP=${tp:.2f}"
        )
        
        return trade
        
        logger.info(
            f"Opened {symbol}: {shares:.4f} shares @ ${entry_price:.2f}, "
            f"TP=${tp:.2f} (NO SL)"
        )
        
        return trade
    
    def _check_and_close_positions(
        self,
        symbol_data: Dict[str, pd.DataFrame],
        current_date: datetime,
        current_idx: int
    ) -> None:
        """
        Verificar y cerrar posiciones (long y short).
        
        Reglas:
        LONG:
        - Si high >= TP => salir en TP
        - Si holding >= max_holding_days => salir en Close
        
        SHORT:
        - Si low <= TP => salir en TP
        - Si holding >= max_holding_days => salir en Close
        """
        for trade in self.open_positions[:]:
            symbol = trade.symbol
            
            if symbol not in symbol_data:
                continue
            
            data = symbol_data[symbol]
            
            if len(data) <= current_idx:
                continue
            
            days_in_position = (current_date - trade.entry_day).days
            high = data['High'].iloc[current_idx]
            low = data['Low'].iloc[current_idx]
            close = data['Close'].iloc[current_idx]
            
            exit_price = None
            reason = None
            
            if trade.direction == 'LONG':
                # TP hit
                if high >= trade.tp:
                    exit_price = trade.tp
                    reason = 'TP'
                # Time exit
                elif days_in_position >= self.max_holding_days:
                    exit_price = close
                    reason = 'TimeExit'
            
            else:  # SHORT
                # TP hit
                if low <= trade.tp:
                    exit_price = trade.tp
                    reason = 'TP'
                # Time exit
                elif days_in_position >= self.max_holding_days:
                    exit_price = close
                    reason = 'TimeExit'
            
            if exit_price is not None:
                self._close_position(trade, current_date, exit_price, reason)
    
    def _close_position(
        self,
        trade: SwingTrade,
        exit_day: datetime,
        exit_price: float,
        reason: str
    ) -> None:
        """Cerrar posición (long o short)."""
        trade.exit_day = exit_day
        trade.exit_price = exit_price
        trade.reason = reason
        
        # Calculate P&L
        if trade.direction == 'LONG':
            pnl_dollar = (exit_price - trade.entry_price) * trade.shares
            pnl_percent = ((exit_price / trade.entry_price) - 1) * 100
        else:  # SHORT
            pnl_dollar = (trade.entry_price - exit_price) * trade.shares
            pnl_percent = ((trade.entry_price / exit_price) - 1) * 100
        
        trade.pnl_dollar = pnl_dollar
        trade.pnl_percent = pnl_percent
        
        self.equity += pnl_dollar
        
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        
        # Only remove if still in open positions
        if trade in self.open_positions:
            self.open_positions.remove(trade)
        
        self.closed_trades.append(trade)
        
        logger.info(
            f"Closed {trade.direction} {trade.symbol}: {trade.shares:.4f} shares @ ${exit_price:.2f}, "
            f"P&L=${pnl_dollar:.2f} ({pnl_percent:.2f}%), reason={reason}"
        )
    
    def run_backtest(
        self,
        start_date: str,
        end_date: str,
        test_start_date: str
    ) -> Dict[str, Any]:
        """Ejecutar backtest completo."""
        logger.info(
            f"Starting backtest (MULTI-ASSET V1): {start_date} to {end_date}, "
            f"test period: {test_start_date} to {end_date}"
        )
        
        # Descargar datos
        logger.info("Downloading market data...")
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        symbol_data = {}
        for symbol in self.symbols:
            data = self.market_data.get_historical_data(
                symbol,
                period='max',
                interval='1d'
            )
            
            if data is None or len(data) == 0:
                logger.error(f"Failed to download data for {symbol}")
                continue
            
            data_index = data.index.tz_localize(None) if data.index.tz is not None else data.index
            data = data[(data_index >= start_dt) & (data_index <= end_dt)]
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)
            symbol_data[symbol] = data
            logger.info(f"Downloaded {symbol}: {len(data)} days")
        
        qqq_data = self.market_data.get_historical_data(
            self.benchmark,
            period='max',
            interval='1d'
        )
        
        if qqq_data is None or len(qqq_data) == 0:
            logger.error(f"Failed to download data for {self.benchmark}")
            return {'error': f'Failed to download {self.benchmark} data'}
        
        qqq_index = qqq_data.index.tz_localize(None) if qqq_data.index.tz is not None else qqq_data.index
        qqq_data = qqq_data[(qqq_index >= start_dt) & (qqq_index <= end_dt)]
        if qqq_data.index.tz is not None:
            qqq_data.index = qqq_data.index.tz_localize(None)
        logger.info(f"Downloaded {self.benchmark}: {len(qqq_data)} days")
        
        trading_days = qqq_data.index
        
        logger.info(f"Running backtest simulation over {len(trading_days)} trading days...")
        
        for i, current_date in enumerate(trading_days):
            if i % 20 == 0:
                logger.debug(f"Processing day {i}/{len(trading_days)}: {current_date}")
            
            # Close positions
            self._check_and_close_positions(symbol_data, current_date, i)
            
            # Determine regime
            regime = self._calculate_market_regime(qqq_data, i)
            
            # Calculate risk budget
            risk_budget = self._calculate_risk_budget(regime, current_date)
            
            if i == 0 or i % 20 == 0:
                logger.info(
                    f"Day {i}: regime={regime}, risk_budget={risk_budget:.2%}, "
                    f"equity=${self.equity:.2f}"
                )
            
            # Record equity
            self.equity_curve.append(self.equity)
            self.dates.append(current_date)
            
            if risk_budget == 0:
                continue
            
            # Calculate relative strength
            rs_scores = self._calculate_relative_strength(symbol_data, qqq_data, i)
            
            # Select symbols based on regime
            selected_symbols, direction = self._select_symbols(rs_scores, regime)
            
            if not selected_symbols:
                continue
            
            allocation_per_symbol = risk_budget / len(selected_symbols)
            
            # Open positions next day
            if i + 1 < len(trading_days):
                entry_day = trading_days[i + 1]
                
                for symbol in selected_symbols:
                    # Check if already have position in this symbol
                    if any(pos.symbol == symbol for pos in self.open_positions):
                        continue
                    
                    if symbol not in symbol_data:
                        continue
                    
                    data = symbol_data[symbol]
                    
                    if len(data) <= i + 1:
                        continue
                    
                    entry_price = data['Open'].iloc[i + 1]
                    
                    self._open_position(
                        symbol=symbol,
                        direction=direction,
                        entry_day=entry_day,
                        entry_price=entry_price,
                        allocation=allocation_per_symbol
                    )
        
        # Cerrar posiciones restantes
        if self.open_positions:
            final_date = trading_days[-1]
            final_idx = len(trading_days) - 1
            
            for trade in self.open_positions[:]:
                if trade.symbol in symbol_data:
                    data = symbol_data[trade.symbol]
                    if len(data) > final_idx:
                        final_price = data['Close'].iloc[final_idx]
                        self._close_position(trade, final_date, final_price, 'EndOfBacktest')
        
        logger.info("Calculating metrics...")
        metrics = self._calculate_metrics(test_start_date)
        
        logger.info(
            f"Backtest complete: {len(self.closed_trades)} trades, "
            f"Final equity: ${self.equity:.2f}, "
            f"Return: {metrics['total_return']:.2f}%"
        )
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': self.equity,
            'metrics': metrics,
            'trades': [self._trade_to_dict(t) for t in self.closed_trades],
            'equity_curve': self.equity_curve,
            'dates': [d.strftime('%Y-%m-%d') for d in self.dates]
        }
    
    def _calculate_metrics(self, test_start_date: str) -> Dict[str, Any]:
        """Calcular métricas de performance (long y short separados)."""
        test_start_dt = datetime.strptime(test_start_date, '%Y-%m-%d')
        
        test_trades = [
            t for t in self.closed_trades
            if t.entry_day >= test_start_dt
        ]
        
        if not test_trades:
            return self._empty_metrics()
        
        # Overall metrics
        total_return = ((self.equity / self.initial_capital) - 1) * 100
        num_trades = len(test_trades)
        
        winners = [t for t in test_trades if t.pnl_dollar > 0]
        losers = [t for t in test_trades if t.pnl_dollar <= 0]
        win_rate = (len(winners) / num_trades) * 100 if num_trades > 0 else 0
        
        avg_winner = np.mean([t.pnl_percent for t in winners]) if winners else 0
        avg_loser = np.mean([t.pnl_percent for t in losers]) if losers else 0
        
        total_wins = sum(t.pnl_dollar for t in winners)
        total_losses = abs(sum(t.pnl_dollar for t in losers))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        loss_rate = 100 - win_rate if num_trades > 0 else 0
        expectancy = (win_rate / 100 * avg_winner) - (loss_rate / 100 * abs(avg_loser))
        
        # Separate long/short metrics
        long_trades = [t for t in test_trades if t.direction == 'LONG']
        short_trades = [t for t in test_trades if t.direction == 'SHORT']
        
        pct_long = (len(long_trades) / num_trades) * 100 if num_trades > 0 else 0
        pct_short = (len(short_trades) / num_trades) * 100 if num_trades > 0 else 0
        
        # Long performance
        if long_trades:
            long_winners = [t for t in long_trades if t.pnl_dollar > 0]
            long_wr = (len(long_winners) / len(long_trades)) * 100
            long_avg_pnl = np.mean([t.pnl_percent for t in long_trades])
        else:
            long_wr = 0
            long_avg_pnl = 0
        
        # Short performance
        if short_trades:
            short_winners = [t for t in short_trades if t.pnl_dollar > 0]
            short_wr = (len(short_winners) / len(short_trades)) * 100
            short_avg_pnl = np.mean([t.pnl_percent for t in short_trades])
        else:
            short_wr = 0
            short_avg_pnl = 0
        
        # Drawdown
        max_dd = 0.0
        peak = self.initial_capital
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        # Exposure
        test_start_idx = next(
            (i for i, d in enumerate(self.dates) if d >= test_start_dt),
            0
        )
        
        days_with_positions = 0
        for i in range(test_start_idx, len(self.dates)):
            date = self.dates[i]
            has_position = any(
                t.entry_day <= date and (t.exit_day is None or t.exit_day >= date)
                for t in self.closed_trades
            )
            if has_position:
                days_with_positions += 1
        
        total_test_days = len(self.dates) - test_start_idx
        exposure = (days_with_positions / total_test_days) * 100 if total_test_days > 0 else 0
        
        # CAGR
        test_days = total_test_days
        years = test_days / 252
        cagr = ((self.equity / self.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # Sharpe
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                daily_return = (self.equity_curve[i] / self.equity_curve[i-1]) - 1
                returns.append(daily_return)
            
            if len(returns) > 0:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'avg_winner': avg_winner,
            'avg_loser': avg_loser,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_dd * 100,
            'exposure': exposure,
            'pct_long_trades': pct_long,
            'pct_short_trades': pct_short,
            'long_win_rate': long_wr,
            'long_avg_pnl': long_avg_pnl,
            'short_win_rate': short_wr,
            'short_avg_pnl': short_avg_pnl,
            'num_long_trades': len(long_trades),
            'num_short_trades': len(short_trades)
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            'total_return': 0.0,
            'cagr': 0.0,
            'num_trades': 0,
            'win_rate': 0.0,
            'avg_winner': 0.0,
            'avg_loser': 0.0,
            'profit_factor': 0.0,
            'expectancy': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'exposure': 0.0,
            'pct_long_trades': 0.0,
            'pct_short_trades': 0.0,
            'long_win_rate': 0.0,
            'long_avg_pnl': 0.0,
            'short_win_rate': 0.0,
            'short_avg_pnl': 0.0,
            'num_long_trades': 0,
            'num_short_trades': 0
        }
    
    def _trade_to_dict(self, trade: SwingTrade) -> Dict[str, Any]:
        """Convertir trade a diccionario."""
        return {
            'symbol': trade.symbol,
            'direction': trade.direction,
            'entry_day': trade.entry_day.strftime('%Y-%m-%d'),
            'entry_price': trade.entry_price,
            'exit_day': trade.exit_day.strftime('%Y-%m-%d') if trade.exit_day else None,
            'exit_price': trade.exit_price,
            'reason': trade.reason,
            'shares': round(trade.shares, 4),
            'pnl_dollar': trade.pnl_dollar,
            'pnl_percent': trade.pnl_percent
        }
