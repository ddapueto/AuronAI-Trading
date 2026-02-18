"""Swing Strategy WITHOUT Stop Loss - Only TP and Time Exit.

Estrategia swing simplificada que:
- NO usa Stop Loss (evita imprecisión con datos diarios)
- Solo sale por Take Profit o Time Exit (10 días)
- Usa market regime filter (QQQ EMA200 + slope + ADX)
- Risk budget dinámico (20% normal, 5% defensivo)
- Kill switch por drawdown (5%, 8%, 10%)
- Selección por fuerza relativa (top 3)
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
    """Representa un trade individual en la estrategia swing."""
    symbol: str
    entry_day: datetime
    entry_price: float
    exit_day: Optional[datetime] = None
    exit_price: Optional[float] = None
    shares: float = 0.0
    tp: float = 0.0
    reason: Optional[str] = None  # 'TP' o 'TimeExit'
    pnl_dollar: Optional[float] = None
    pnl_percent: Optional[float] = None


class SwingNoSLStrategy:
    """
    Estrategia swing SIN Stop Loss.
    
    Features:
    - NO Stop Loss (solo TP y Time Exit)
    - Market regime filter usando QQQ
    - Risk budget dinámico (20% normal, 5% defensivo)
    - Kill switch por drawdown
    - Selección por fuerza relativa
    - TP fijo 5%
    - Holding máximo 10 días
    """
    
    def __init__(
        self,
        symbols: List[str],
        benchmark: str = 'QQQ',
        initial_capital: float = 1000.0,
        base_risk_budget: float = 0.20,
        defensive_risk_budget: float = 0.05,
        top_k: int = 3,
        tp_multiplier: float = 1.05,
        max_holding_days: int = 10,
        dd_threshold_1: float = 0.05,
        dd_threshold_2: float = 0.08,
        dd_threshold_3: float = 0.10,
        cooldown_days: int = 10
    ):
        """
        Inicializar estrategia swing sin SL.
        
        Args:
            symbols: Lista de símbolos a tradear
            benchmark: Símbolo de benchmark para market regime (default: 'QQQ')
            initial_capital: Capital inicial en USD
            base_risk_budget: Risk budget normal (default: 0.20 = 20%)
            defensive_risk_budget: Risk budget defensivo (default: 0.05 = 5%)
            top_k: Número de símbolos a seleccionar por día (default: 3)
            tp_multiplier: Multiplicador para take profit (default: 1.05 = 5%)
            max_holding_days: Días máximos de holding (default: 10)
            dd_threshold_1: Drawdown threshold 1 (default: 0.05 = 5%)
            dd_threshold_2: Drawdown threshold 2 (default: 0.08 = 8%)
            dd_threshold_3: Drawdown threshold 3 (default: 0.10 = 10%)
            cooldown_days: Días de cooldown después de dd_threshold_3 (default: 10)
        """
        self.symbols = symbols
        self.benchmark = benchmark
        self.initial_capital = initial_capital
        self.base_risk_budget = base_risk_budget
        self.defensive_risk_budget = defensive_risk_budget
        self.top_k = top_k
        self.tp_multiplier = tp_multiplier
        self.max_holding_days = max_holding_days
        self.dd_threshold_1 = dd_threshold_1
        self.dd_threshold_2 = dd_threshold_2
        self.dd_threshold_3 = dd_threshold_3
        self.cooldown_days = cooldown_days
        
        # Market data provider
        self.market_data = MarketDataProvider()
        
        # State
        self.equity = initial_capital
        self.peak_equity = initial_capital
        self.open_positions: List[SwingTrade] = []
        self.closed_trades: List[SwingTrade] = []
        self.equity_curve: List[float] = []
        self.dates: List[datetime] = []
        self.cooldown_until: Optional[datetime] = None
        
        logger.info(
            f"SwingNoSLStrategy initialized: symbols={symbols}, "
            f"benchmark={benchmark}, capital=${initial_capital}, NO STOP LOSS"
        )
    
    def _calculate_market_regime(
        self,
        qqq_data: pd.DataFrame,
        current_idx: int
    ) -> bool:
        """Calcular market regime usando QQQ."""
        if current_idx < 200:
            return False
        
        ema200 = ta.ema(qqq_data['Close'], length=200)
        if ema200 is None or len(ema200) <= current_idx:
            return False
        
        current_close = qqq_data['Close'].iloc[current_idx]
        current_ema200 = ema200.iloc[current_idx]
        close_above_ema = current_close > current_ema200
        
        if current_idx < 220:
            slope_positive = False
        else:
            slope20 = ema200.iloc[current_idx] - ema200.iloc[current_idx - 20]
            slope_positive = slope20 > 0
        
        adx = ta.adx(
            qqq_data['High'],
            qqq_data['Low'],
            qqq_data['Close'],
            length=14
        )
        
        if adx is None or len(adx) <= current_idx:
            adx_ok = False
        else:
            adx_col = [col for col in adx.columns if col.startswith('ADX')][0]
            adx_value = adx[adx_col].iloc[current_idx]
            adx_ok = adx_value >= 15
        
        market_ok = close_above_ema and slope_positive and adx_ok
        
        if current_idx % 20 == 0:
            logger.info(f"Market Regime (day {current_idx}): {market_ok}")
        
        return market_ok
    
    def _calculate_risk_budget(
        self,
        market_ok: bool,
        current_date: datetime
    ) -> float:
        """Calcular risk budget dinámico."""
        if self.cooldown_until is not None and current_date < self.cooldown_until:
            return 0.0
        
        if market_ok:
            risk_budget = self.base_risk_budget
        else:
            risk_budget = self.defensive_risk_budget
        
        dd = (self.peak_equity - self.equity) / self.peak_equity if self.peak_equity > 0 else 0
        
        if dd >= self.dd_threshold_3:
            logger.warning(f"Drawdown {dd:.2%} >= {self.dd_threshold_3:.2%}: PAUSING")
            self.cooldown_until = current_date + timedelta(days=self.cooldown_days)
            return 0.0
        elif dd >= self.dd_threshold_2:
            risk_budget = min(risk_budget, 0.05)
        elif dd >= self.dd_threshold_1:
            risk_budget = min(risk_budget, 0.10)
        
        return risk_budget
    
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
    
    def _select_top_symbols(
        self,
        rs_scores: Dict[str, float]
    ) -> List[str]:
        """Seleccionar top K símbolos."""
        if not rs_scores:
            return []
        
        sorted_symbols = sorted(rs_scores.items(), key=lambda x: x[1], reverse=True)
        selected = [symbol for symbol, score in sorted_symbols[:self.top_k]]
        
        return selected
    
    def _open_position(
        self,
        symbol: str,
        entry_day: datetime,
        entry_price: float,
        allocation: float
    ) -> Optional[SwingTrade]:
        """Abrir nueva posición (sin SL)."""
        tp = entry_price * self.tp_multiplier
        position_value = self.equity * allocation
        shares = position_value / entry_price
        
        if shares < 0.01:
            return None
        
        trade = SwingTrade(
            symbol=symbol,
            entry_day=entry_day,
            entry_price=entry_price,
            shares=shares,
            tp=tp
        )
        
        self.open_positions.append(trade)
        
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
        Verificar y cerrar posiciones.
        
        Reglas (SIN Stop Loss):
        1. Si high >= TP => salir en TP
        2. Si holding >= max_holding_days => salir en Close
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
            close = data['Close'].iloc[current_idx]
            
            exit_price = None
            reason = None
            
            # Regla 1: Si toca TP
            if high >= trade.tp:
                exit_price = trade.tp
                reason = 'TP'
            
            # Regla 2: Max holding period
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
        """Cerrar posición."""
        trade.exit_day = exit_day
        trade.exit_price = exit_price
        trade.reason = reason
        
        pnl_dollar = (exit_price - trade.entry_price) * trade.shares
        pnl_percent = ((exit_price / trade.entry_price) - 1) * 100
        
        trade.pnl_dollar = pnl_dollar
        trade.pnl_percent = pnl_percent
        
        self.equity += pnl_dollar
        
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        
        self.open_positions.remove(trade)
        self.closed_trades.append(trade)
        
        logger.info(
            f"Closed {trade.symbol}: {trade.shares:.4f} shares @ ${exit_price:.2f}, "
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
            f"Starting backtest (NO SL): {start_date} to {end_date}, "
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
            
            self._check_and_close_positions(symbol_data, current_date, i)
            market_ok = self._calculate_market_regime(qqq_data, i)
            risk_budget = self._calculate_risk_budget(market_ok, current_date)
            
            if i == 0 or i % 20 == 0:
                logger.info(f"Day {i}: market_ok={market_ok}, risk_budget={risk_budget:.2%}, equity=${self.equity:.2f}")
            
            self.equity_curve.append(self.equity)
            self.dates.append(current_date)
            
            if risk_budget == 0:
                continue
            
            rs_scores = self._calculate_relative_strength(symbol_data, qqq_data, i)
            selected_symbols = self._select_top_symbols(rs_scores)
            
            if not selected_symbols:
                continue
            
            allocation_per_symbol = risk_budget / len(selected_symbols)
            
            if i + 1 < len(trading_days):
                entry_day = trading_days[i + 1]
                
                for symbol in selected_symbols:
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
        """Calcular métricas de performance."""
        test_start_dt = datetime.strptime(test_start_date, '%Y-%m-%d')
        
        test_trades = [
            t for t in self.closed_trades
            if t.entry_day >= test_start_dt
        ]
        
        if not test_trades:
            return {
                'total_return': 0.0,
                'num_trades': 0,
                'win_rate': 0.0,
                'avg_winner': 0.0,
                'avg_loser': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'exposure': 0.0
            }
        
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
        
        max_dd = 0.0
        peak = self.initial_capital
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
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
        
        test_days = total_test_days
        years = test_days / 252
        cagr = ((self.equity / self.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # Calcular Expectancy
        # Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
        loss_rate = 100 - win_rate if num_trades > 0 else 0
        expectancy = (win_rate / 100 * avg_winner) - (loss_rate / 100 * abs(avg_loser))
        
        # Calcular Sharpe Ratio
        # Sharpe = (Return - Risk Free Rate) / Std Dev of Returns
        # Asumimos risk free rate = 0 para simplificar
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
            'exposure': exposure
        }
    
    def _trade_to_dict(self, trade: SwingTrade) -> Dict[str, Any]:
        """Convertir trade a diccionario."""
        return {
            'symbol': trade.symbol,
            'entry_day': trade.entry_day.strftime('%Y-%m-%d'),
            'entry_price': trade.entry_price,
            'exit_day': trade.exit_day.strftime('%Y-%m-%d') if trade.exit_day else None,
            'exit_price': trade.exit_price,
            'reason': trade.reason,
            'shares': round(trade.shares, 4),
            'pnl_dollar': trade.pnl_dollar,
            'pnl_percent': trade.pnl_percent
        }
