"""Backtesting engine for testing trading strategies on historical data."""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import pandas as pd
import numpy as np
import logging

from auronai.data.market_data_provider import MarketDataProvider
from auronai.indicators.technical_indicators import TechnicalIndicators
from auronai.analysis.signal_generator import SignalGenerator
from auronai.risk.risk_manager import RiskManager

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade in the backtest."""
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: Optional[float]
    shares: int
    stop_loss: float
    take_profit: float
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    status: str = 'open'  # 'open', 'closed_profit', 'closed_loss', 'closed_stop', 'closed_target'


class BacktestEngine:
    """
    Backtesting engine to simulate trading strategies on historical data.
    
    Supports multiple strategies, risk management, transaction costs,
    and comprehensive performance metrics.
    
    **Validates: Requirements 5.1**
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,  # 0.1%
        slippage_rate: float = 0.001,    # 0.1%
        max_risk_per_trade: float = 0.02,
        max_position_size: float = 0.20
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital in USD
            commission_rate: Commission as decimal (0.001 = 0.1%)
            slippage_rate: Slippage as decimal (0.001 = 0.1%)
            max_risk_per_trade: Maximum risk per trade as decimal
            max_position_size: Maximum position size as decimal
            
        **Validates: Requirements 5.1, 5.11**
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.max_risk_per_trade = max_risk_per_trade
        self.max_position_size = max_position_size
        
        # Components
        self.market_data = MarketDataProvider()
        self.indicators = TechnicalIndicators(advanced_mode=False)
        self.signal_generator = SignalGenerator()
        
        # State
        self.cash = initial_capital
        self.portfolio_value = initial_capital
        self.positions: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.equity_curve: List[float] = [initial_capital]
        self.dates: List[datetime] = []
        
        logger.info(
            f"BacktestEngine initialized: capital=${initial_capital}, "
            f"commission={commission_rate*100}%, slippage={slippage_rate*100}%"
        )

    
    def _apply_transaction_costs(
        self,
        price: float,
        shares: int,
        side: str
    ) -> Tuple[float, float]:
        """
        Apply commission and slippage to a trade.
        
        Args:
            price: Base price
            shares: Number of shares
            side: 'buy' or 'sell'
            
        Returns:
            Tuple of (adjusted_price, total_cost)
            
        **Validates: Requirements 5.11**
        """
        # Apply slippage (worse price for trader)
        if side == 'buy':
            adjusted_price = price * (1 + self.slippage_rate)
        else:  # sell
            adjusted_price = price * (1 - self.slippage_rate)
        
        # Calculate commission
        trade_value = adjusted_price * shares
        commission = trade_value * self.commission_rate
        
        # Total cost includes commission
        if side == 'buy':
            total_cost = trade_value + commission
        else:  # sell
            total_cost = trade_value - commission
        
        return adjusted_price, total_cost
    
    def _calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        current_portfolio_value: float
    ) -> int:
        """
        Calculate position size using risk management.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            current_portfolio_value: Current portfolio value
            
        Returns:
            Number of shares to trade
            
        **Validates: Requirements 5.3**
        """
        # Use RiskManager for position sizing
        risk_manager = RiskManager(
            portfolio_value=current_portfolio_value,
            max_risk_per_trade=self.max_risk_per_trade,
            max_position_size=self.max_position_size
        )
        
        # Use 60% win probability and 2:1 R/R for backtesting
        shares = risk_manager.calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            win_probability=0.6,
            rr_ratio=2.0
        )
        
        # Ensure we have enough cash
        cost_estimate = entry_price * shares * (1 + self.commission_rate + self.slippage_rate)
        if cost_estimate > self.cash:
            # Reduce shares to fit available cash
            shares = int(self.cash / (entry_price * (1 + self.commission_rate + self.slippage_rate)))
        
        return max(0, shares)
    
    def _open_position(
        self,
        date: datetime,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> Optional[Trade]:
        """
        Open a new position.
        
        Args:
            date: Entry date
            symbol: Stock symbol
            side: 'long' or 'short'
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Trade object or None if position cannot be opened
        """
        # Calculate position size
        shares = self._calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            current_portfolio_value=self.portfolio_value
        )
        
        if shares == 0:
            logger.debug(f"Cannot open position: insufficient capital")
            return None
        
        # Apply transaction costs
        adjusted_price, total_cost = self._apply_transaction_costs(
            price=entry_price,
            shares=shares,
            side='buy' if side == 'long' else 'sell'
        )
        
        # Check if we have enough cash
        if total_cost > self.cash:
            logger.debug(f"Cannot open position: insufficient cash (need ${total_cost:.2f}, have ${self.cash:.2f})")
            return None
        
        # Deduct cash
        self.cash -= total_cost
        
        # Create trade
        trade = Trade(
            entry_date=date,
            exit_date=None,
            symbol=symbol,
            side=side,
            entry_price=adjusted_price,
            exit_price=None,
            shares=shares,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status='open'
        )
        
        self.positions.append(trade)
        
        logger.debug(
            f"Opened {side} position: {shares} shares of {symbol} @ ${adjusted_price:.2f}, "
            f"SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}"
        )
        
        return trade
    
    def _close_position(
        self,
        trade: Trade,
        date: datetime,
        exit_price: float,
        reason: str
    ) -> None:
        """
        Close an existing position.
        
        Args:
            trade: Trade to close
            date: Exit date
            exit_price: Exit price
            reason: Reason for closing ('stop', 'target', 'signal', 'end')
        """
        # Apply transaction costs
        adjusted_price, proceeds = self._apply_transaction_costs(
            price=exit_price,
            shares=trade.shares,
            side='sell' if trade.side == 'long' else 'buy'
        )
        
        # Add proceeds to cash
        self.cash += proceeds
        
        # Calculate P&L
        if trade.side == 'long':
            pnl = (adjusted_price - trade.entry_price) * trade.shares
        else:  # short
            pnl = (trade.entry_price - adjusted_price) * trade.shares
        
        # Subtract transaction costs from P&L
        entry_cost = trade.entry_price * trade.shares * self.commission_rate
        exit_cost = adjusted_price * trade.shares * self.commission_rate
        pnl -= (entry_cost + exit_cost)
        
        pnl_percent = (pnl / (trade.entry_price * trade.shares)) * 100
        
        # Update trade
        trade.exit_date = date
        trade.exit_price = adjusted_price
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        
        if reason == 'stop':
            trade.status = 'closed_stop'
        elif reason == 'target':
            trade.status = 'closed_target'
        elif pnl > 0:
            trade.status = 'closed_profit'
        else:
            trade.status = 'closed_loss'
        
        # Move to closed trades
        self.positions.remove(trade)
        self.closed_trades.append(trade)
        
        logger.debug(
            f"Closed {trade.side} position: {trade.shares} shares of {trade.symbol} @ ${adjusted_price:.2f}, "
            f"P&L: ${pnl:.2f} ({pnl_percent:.2f}%), reason: {reason}"
        )
    
    def _check_stops_and_targets(
        self,
        date: datetime,
        current_price: float,
        high_price: Optional[float] = None,
        low_price: Optional[float] = None,
        indicators: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Check if any open positions should be closed based on EOD strategy.
        
        EOD (End of Day) Strategy with Protection Rules:
        
        Exit conditions:
        1. Manual exit signal from strategy (SELL signal)
        2. Maximum holding period (60 days) - prevents being stuck
        3. Trend reversal (EMA 20 crosses below EMA 50) - exit on trend change
        
        Args:
            date: Current date
            current_price: Current close price
            high_price: Ignored in EOD strategy
            low_price: Ignored in EOD strategy
            indicators: Current indicator values for trend detection
            
        **Validates: Requirements 5.3 - EOD realistic execution with protection**
        """
        max_holding_days = 60  # Maximum days to hold a position
        
        for trade in self.positions[:]:  # Copy list to allow modification
            # Calculate days in position
            days_in_position = (date - trade.entry_date).days
            
            # RULE 1: Maximum holding period (60 days)
            if days_in_position >= max_holding_days:
                logger.info(
                    f"Closing {trade.symbol} after {days_in_position} days "
                    f"(max holding period reached)"
                )
                self._close_position(trade, date, current_price, 'max_days')
                continue
            
            # RULE 2: Trend reversal detection (EMA crossover)
            if indicators:
                ema_20 = indicators.get('ema_20')
                ema_50 = indicators.get('ema_50')
                
                if ema_20 is not None and ema_50 is not None:
                    if trade.side == 'long':
                        # For long positions: exit if EMA 20 crosses below EMA 50
                        if ema_20 < ema_50:
                            logger.info(
                                f"Closing {trade.symbol} on trend reversal "
                                f"(EMA 20 < EMA 50)"
                            )
                            self._close_position(trade, date, current_price, 'trend_reversal')
                            continue
                    else:  # short
                        # For short positions: exit if EMA 20 crosses above EMA 50
                        if ema_20 > ema_50:
                            logger.info(
                                f"Closing {trade.symbol} on trend reversal "
                                f"(EMA 20 > EMA 50)"
                            )
                            self._close_position(trade, date, current_price, 'trend_reversal')
                            continue
    
    def _update_portfolio_value(self, current_price: float) -> None:
        """
        Update portfolio value based on current price.
        
        Args:
            current_price: Current market price
        """
        # Calculate value of open positions
        positions_value = 0.0
        for trade in self.positions:
            if trade.side == 'long':
                positions_value += current_price * trade.shares
            else:  # short
                # For shorts, value is entry_price * shares - (current_price - entry_price) * shares
                positions_value += (2 * trade.entry_price - current_price) * trade.shares
        
        self.portfolio_value = self.cash + positions_value

    
    def run_backtest(
        self,
        symbol: str,
        strategy: str = 'rsi',
        period: str = '1y',
        interval: str = '1d',
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run backtest for a symbol using specified strategy.
        
        Args:
            symbol: Stock symbol to backtest
            strategy: Strategy name ('rsi', 'macd', 'ema_cross', 'combo', 'professional')
            period: Historical period to test
            interval: Data interval
            strategy_params: Optional parameters for strategy configuration
            
        Returns:
            Dictionary with backtest results including metrics and trades
            
        **Validates: Requirements 5.1, 5.2**
        """
        # Set default strategy parameters
        if strategy_params is None:
            strategy_params = {}
        
        # Default RSI thresholds (more aggressive than 30/70)
        self.rsi_oversold = strategy_params.get('rsi_oversold', 35)
        self.rsi_overbought = strategy_params.get('rsi_overbought', 65)
        logger.info(f"Starting backtest: {symbol}, strategy={strategy}, period={period}")
        
        # Reset state
        self.cash = self.initial_capital
        self.portfolio_value = self.initial_capital
        self.positions = []
        self.closed_trades = []
        self.equity_curve = [self.initial_capital]
        self.dates = []
        
        # Get historical data
        data = self.market_data.get_historical_data(symbol, period=period, interval=interval)
        
        if data is None or len(data) < 50:
            logger.error(f"Insufficient data for {symbol}")
            return {
                'symbol': symbol,
                'strategy': strategy,
                'error': 'Insufficient data'
            }
        
        logger.info(f"Backtesting {symbol} with {len(data)} data points")
        
        # Iterate through data day by day
        for i in range(50, len(data)):  # Start at 50 to have enough data for indicators
            current_date = data.index[i]
            current_data = data.iloc[:i+1]
            current_price = float(data['Close'].iloc[i])
            high_price = float(data['High'].iloc[i])
            low_price = float(data['Low'].iloc[i])
            
            # Calculate indicators
            indicators_dict = self.indicators.calculate_all_indicators(current_data)
            if not indicators_dict:
                continue
            
            # Flatten indicators
            flat_indicators = self._flatten_indicators(indicators_dict, current_price)
            
            # Check stops and targets for open positions using EOD protection rules
            self._check_stops_and_targets(
                current_date, 
                current_price, 
                high_price, 
                low_price,
                flat_indicators
            )
            
            # Generate signal based on strategy
            if strategy == 'rsi':
                signal_action = self._evaluate_rsi_signal(flat_indicators)
            elif strategy == 'macd':
                signal_action = self._evaluate_macd_signal(flat_indicators)
            elif strategy == 'ema_cross':
                signal_action = self._evaluate_ema_signal(flat_indicators)
            elif strategy == 'combo':
                signal_action = self._evaluate_combo_signal(flat_indicators)
            elif strategy == 'professional':
                signal_action = self._evaluate_professional_signal(flat_indicators, strategy_params)
            else:
                signal = self.signal_generator.generate_signal(flat_indicators, strategy=strategy)
                signal_action = signal['action']
            
            # Execute strategy
            if signal_action == 'BUY' and len(self.positions) == 0:
                # Calculate stop loss and take profit
                atr = flat_indicators.get('atr', current_price * 0.02)
                stop_loss = current_price - (2 * atr)
                take_profit = current_price + (4 * atr)  # 2:1 R/R
                
                self._open_position(
                    date=current_date,
                    symbol=symbol,
                    side='long',
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
            
            elif signal_action == 'SELL' and len(self.positions) > 0:
                # Close all positions on sell signal
                for trade in self.positions[:]:
                    self._close_position(trade, current_date, current_price, 'signal')
            
            # Update portfolio value
            self._update_portfolio_value(current_price)
            
            # Record equity curve
            self.equity_curve.append(self.portfolio_value)
            self.dates.append(current_date)
        
        # Close any remaining positions at end
        if len(self.positions) > 0:
            final_price = float(data['Close'].iloc[-1])
            final_date = data.index[-1]
            for trade in self.positions[:]:
                self._close_position(trade, final_date, final_price, 'end')
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        logger.info(
            f"Backtest complete: {len(self.closed_trades)} trades, "
            f"Final value: ${self.portfolio_value:.2f}, "
            f"Return: {metrics['total_return']:.2f}%"
        )
        
        return {
            'symbol': symbol,
            'strategy': strategy,
            'period': period,
            'initial_capital': self.initial_capital,
            'final_value': self.portfolio_value,
            'metrics': metrics,
            'trades': [self._trade_to_dict(t) for t in self.closed_trades],
            'equity_curve': self.equity_curve,
            'dates': [d.isoformat() for d in self.dates]
        }
    
    def _evaluate_rsi_signal(self, indicators: Dict[str, Any]) -> str:
        """Evaluate RSI strategy with configurable thresholds."""
        rsi = indicators.get("rsi")
        
        if rsi is None:
            return "HOLD"
            
        if rsi < self.rsi_oversold:
            return "BUY"  # Oversold
        elif rsi > self.rsi_overbought:
            return "SELL"  # Overbought
        else:
            return "HOLD"
    
    def _evaluate_macd_signal(self, indicators: Dict[str, Any]) -> str:
        """Evaluate MACD crossover strategy."""
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        
        if None in [macd, macd_signal]:
            return "HOLD"
            
        if macd > macd_signal:
            return "BUY"  # MACD above signal
        elif macd < macd_signal:
            return "SELL"  # MACD below signal
        else:
            return "HOLD"
    
    def _evaluate_ema_signal(self, indicators: Dict[str, Any]) -> str:
        """Evaluate EMA trend following strategy."""
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        
        if None in [ema_20, ema_50]:
            return "HOLD"
            
        if ema_20 > ema_50:
            return "BUY"  # Uptrend
        elif ema_20 < ema_50:
            return "SELL"  # Downtrend
        else:
            return "HOLD"
    
    def _evaluate_combo_signal(self, indicators: Dict[str, Any]) -> str:
        """
        Evaluate combo strategy using VOTING SYSTEM with uncorrelated clusters.
        
        4 Independent Clusters (1 vote each):
        1. TREND Cluster (EMA)
        2. MOMENTUM Cluster (RSI)
        3. VOLATILITY Cluster (Bollinger Bands)
        4. VOLUME Cluster (OBV)
        
        BALANCED APPROACH:
        - Requires 3 of 4 votes (75% agreement) - maintains quality
        - Slightly more sensitive thresholds - generates more signals
        - Works with EOD protection rules (60 days + trend reversal)
        """
        bullish_votes = 0
        bearish_votes = 0
        total_votes = 0
        
        # === CLUSTER 1: TREND (EMA) ===
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        
        if ema_20 is not None and ema_50 is not None:
            total_votes += 1
            if ema_20 > ema_50:
                bullish_votes += 1  # Uptrend
            else:
                bearish_votes += 1  # Downtrend
        
        # === CLUSTER 2: MOMENTUM (RSI) - SLIGHTLY MORE SENSITIVE ===
        rsi = indicators.get("rsi")
        if rsi is not None:
            total_votes += 1
            # Adjusted thresholds: 42/58 (middle ground between 40/60 and 45/55)
            if rsi < 42:  # Oversold or pullback in uptrend
                bullish_votes += 1
            elif rsi > 58:  # Overbought or rally in downtrend
                bearish_votes += 1
            # RSI 42-58 = neutral, no vote
        
        # === CLUSTER 3: VOLATILITY (Bollinger Bands) - SLIGHTLY MORE SENSITIVE ===
        close = indicators.get("close")
        bb_lower = indicators.get("bb_lower")
        bb_upper = indicators.get("bb_upper")
        bb_middle = indicators.get("bb_middle")
        
        if None not in [close, bb_lower, bb_upper, bb_middle]:
            total_votes += 1
            band_width = bb_upper - bb_lower
            if band_width > 0:
                # Position within bands
                position = (close - bb_lower) / band_width
                
                # Adjusted thresholds: 0.25/0.75 (middle ground between 0.2/0.8 and 0.3/0.7)
                if position < 0.25:  # Near lower band
                    bullish_votes += 1
                elif position > 0.75:  # Near upper band
                    bearish_votes += 1
                # 0.25-0.75 = neutral, no vote
        
        # === CLUSTER 4: VOLUME (OBV) ===
        obv = indicators.get("obv")
        obv_prev = indicators.get("obv_prev")
        if obv is not None and obv_prev is not None:
            total_votes += 1
            if obv > obv_prev:  # Volume accumulation (bullish)
                bullish_votes += 1
            elif obv < obv_prev:  # Volume distribution (bearish)
                bearish_votes += 1
            # obv == obv_prev = neutral, no vote
        
        # BALANCED: Require 3 of 4 votes (75% agreement)
        # Maintains quality while slightly more sensitive thresholds generate more signals
        min_votes_required = 3
        
        if bullish_votes >= min_votes_required:
            return "BUY"
        elif bearish_votes >= min_votes_required:
            return "SELL"
        else:
            return "HOLD"
        min_votes_required = 3
        
        if bullish_votes >= min_votes_required:
            return "BUY"
        elif bearish_votes >= min_votes_required:
            return "SELL"
        else:
            return "HOLD"
    
    def _evaluate_professional_signal(
        self,
        indicators: Dict[str, Any],
        strategy_params: Dict[str, Any]
    ) -> str:
        """
        Professional multi-indicator strategy with weighted scoring.
        
        Uses all 15+ indicators with intelligent weighting:
        - Trend indicators (EMA, MACD): 40%
        - Momentum indicators (RSI, Stochastic): 30%
        - Volatility indicators (Bollinger, ATR): 20%
        - Volume indicators (OBV): 10%
        """
        bullish_score = 0.0
        bearish_score = 0.0
        
        # Get weights from params or use defaults
        weights = strategy_params.get('weights', {
            'trend': 0.40,
            'momentum': 0.30,
            'volatility': 0.20,
            'volume': 0.10
        })
        
        # === TREND INDICATORS (40%) ===
        trend_weight = weights['trend']
        
        # EMA Analysis (20%)
        ema_20 = indicators.get("ema_20")
        ema_50 = indicators.get("ema_50")
        ema_200 = indicators.get("ema_200")
        close = indicators.get("close")
        
        if None not in [ema_20, ema_50, close]:
            ema_score = 0.0
            # Strong trend: all EMAs aligned
            if ema_200 is not None:
                if ema_20 > ema_50 > ema_200 and close > ema_20:
                    ema_score = 1.0  # Strong uptrend
                elif ema_20 < ema_50 < ema_200 and close < ema_20:
                    ema_score = -1.0  # Strong downtrend
                elif ema_20 > ema_50 and close > ema_20:
                    ema_score = 0.7  # Moderate uptrend
                elif ema_20 < ema_50 and close < ema_20:
                    ema_score = -0.7  # Moderate downtrend
            else:
                if ema_20 > ema_50 and close > ema_20:
                    ema_score = 0.7
                elif ema_20 < ema_50 and close < ema_20:
                    ema_score = -0.7
            
            if ema_score > 0:
                bullish_score += trend_weight * 0.5 * ema_score
            else:
                bearish_score += trend_weight * 0.5 * abs(ema_score)
        
        # MACD Analysis (20%)
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        
        if macd is not None and macd_signal is not None:
            macd_diff = macd - macd_signal
            # Normalize to -1 to 1 range
            macd_strength = min(max(macd_diff / 2.0, -1.0), 1.0)
            
            if macd_strength > 0:
                bullish_score += trend_weight * 0.5 * macd_strength
            else:
                bearish_score += trend_weight * 0.5 * abs(macd_strength)
        
        # === MOMENTUM INDICATORS (30%) ===
        momentum_weight = weights['momentum']
        
        # RSI Analysis (15%)
        rsi = indicators.get("rsi")
        if rsi is not None:
            if rsi < 30:
                bullish_score += momentum_weight * 0.5 * 1.0  # Strong oversold
            elif rsi < 40:
                bullish_score += momentum_weight * 0.5 * 0.6  # Moderate oversold
            elif rsi > 70:
                bearish_score += momentum_weight * 0.5 * 1.0  # Strong overbought
            elif rsi > 60:
                bearish_score += momentum_weight * 0.5 * 0.6  # Moderate overbought
        
        # Stochastic Analysis (15%)
        stoch_k = indicators.get("stochastic_k")
        if stoch_k is not None:
            if stoch_k < 20:
                bullish_score += momentum_weight * 0.5 * 1.0
            elif stoch_k < 30:
                bullish_score += momentum_weight * 0.5 * 0.6
            elif stoch_k > 80:
                bearish_score += momentum_weight * 0.5 * 1.0
            elif stoch_k > 70:
                bearish_score += momentum_weight * 0.5 * 0.6
        
        # === VOLATILITY INDICATORS (20%) ===
        volatility_weight = weights['volatility']
        
        # Bollinger Bands Analysis (15%)
        bb_lower = indicators.get("bb_lower")
        bb_upper = indicators.get("bb_upper")
        bb_middle = indicators.get("bb_middle")
        
        if None not in [close, bb_lower, bb_upper, bb_middle]:
            band_width = bb_upper - bb_lower
            if band_width > 0:
                # Position within bands (0 = lower, 1 = upper)
                position = (close - bb_lower) / band_width
                
                if position < 0.1:
                    bullish_score += volatility_weight * 0.75 * 1.0  # Very oversold
                elif position < 0.3:
                    bullish_score += volatility_weight * 0.75 * 0.6  # Oversold
                elif position > 0.9:
                    bearish_score += volatility_weight * 0.75 * 1.0  # Very overbought
                elif position > 0.7:
                    bearish_score += volatility_weight * 0.75 * 0.6  # Overbought
        
        # ATR for volatility context (5%)
        atr = indicators.get("atr")
        if atr is not None and close is not None:
            # High volatility = more caution
            volatility_ratio = atr / close
            if volatility_ratio > 0.03:  # High volatility
                # Reduce both scores slightly
                reduction = volatility_weight * 0.25 * 0.3
                bullish_score = max(0, bullish_score - reduction)
                bearish_score = max(0, bearish_score - reduction)
        
        # === VOLUME INDICATORS (10%) ===
        volume_weight = weights['volume']
        
        # OBV Analysis
        obv = indicators.get("obv")
        if obv is not None:
            # Simple: positive OBV trend = bullish
            if obv > 0:
                bullish_score += volume_weight * 0.5
            else:
                bearish_score += volume_weight * 0.5
        
        # === DECISION LOGIC ===
        # Require minimum score threshold
        min_threshold = strategy_params.get('min_threshold', 0.25)
        
        net_score = bullish_score - bearish_score
        
        if bullish_score > min_threshold and net_score > 0.15:
            return "BUY"
        elif bearish_score > min_threshold and net_score < -0.15:
            return "SELL"
        else:
            return "HOLD"
    
    def _flatten_indicators(
        self,
        indicators_dict: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """Flatten nested indicator dictionary."""
        flat = {'close': current_price}
        
        for key, value in indicators_dict.items():
            if isinstance(value, dict):
                if 'value' in value:
                    flat[key] = value['value']
                if 'previous' in value:
                    flat[f'{key}_prev'] = value['previous']
                if key == 'macd':
                    flat['macd'] = value.get('value')
                    flat['macd_signal'] = value.get('signal')
                elif key == 'bollinger_bands':
                    flat['bb_upper'] = value.get('upper')
                    flat['bb_middle'] = value.get('middle')
                    flat['bb_lower'] = value.get('lower')
            else:
                flat[key] = value
        
        return flat
    
    def _trade_to_dict(self, trade: Trade) -> Dict[str, Any]:
        """Convert Trade object to dictionary."""
        return {
            'entry_date': trade.entry_date.isoformat() if trade.entry_date else None,
            'exit_date': trade.exit_date.isoformat() if trade.exit_date else None,
            'symbol': trade.symbol,
            'side': trade.side,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'shares': trade.shares,
            'stop_loss': trade.stop_loss,
            'take_profit': trade.take_profit,
            'pnl': trade.pnl,
            'pnl_percent': trade.pnl_percent,
            'status': trade.status
        }

    
    def _calculate_metrics(self) -> Dict[str, float]:
        """
        Calculate comprehensive backtest metrics.
        
        Returns:
            Dictionary with performance metrics
            
        **Validates: Requirements 5.4, 5.5, 5.6, 5.7, 5.8**
        """
        if len(self.closed_trades) == 0:
            return {
                'total_return': 0.0,
                'total_return_percent': 0.0,
                'annualized_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_percent': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'avg_trade_return': 0.0
            }
        
        # Total return
        total_return = self.portfolio_value - self.initial_capital
        total_return_percent = (total_return / self.initial_capital) * 100
        
        # Annualized return (assuming 252 trading days per year)
        days = len(self.equity_curve)
        years = days / 252.0
        if years > 0:
            annualized_return = ((self.portfolio_value / self.initial_capital) ** (1 / years) - 1) * 100
        else:
            annualized_return = 0.0
        
        # Sharpe Ratio
        returns = pd.Series(self.equity_curve).pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Max Drawdown
        equity_series = pd.Series(self.equity_curve)
        cumulative_max = equity_series.cummax()
        drawdown = equity_series - cumulative_max
        max_drawdown = drawdown.min()
        max_drawdown_percent = (max_drawdown / cumulative_max.max()) * 100 if cumulative_max.max() > 0 else 0.0
        
        # Win Rate and Profit Factor
        winning_trades = [t for t in self.closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl and t.pnl <= 0]
        
        total_trades = len(self.closed_trades)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
        
        gross_profit = sum(t.pnl for t in winning_trades if t.pnl)
        gross_loss = abs(sum(t.pnl for t in losing_trades if t.pnl))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0
        
        # Average win/loss
        avg_win = (gross_profit / len(winning_trades)) if len(winning_trades) > 0 else 0.0
        avg_loss = (gross_loss / len(losing_trades)) if len(losing_trades) > 0 else 0.0
        
        # Largest win/loss
        largest_win = max((t.pnl for t in winning_trades if t.pnl), default=0.0)
        largest_loss = min((t.pnl for t in losing_trades if t.pnl), default=0.0)
        
        # Average trade return (percentage)
        avg_trade_return = (sum(t.pnl_percent for t in self.closed_trades if t.pnl_percent) / total_trades) if total_trades > 0 else 0.0
        
        return {
            'total_return': total_return,
            'total_return_percent': total_return_percent,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_percent': max_drawdown_percent,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_trade_return': avg_trade_return
        }
    
    def compare_strategies(
        self,
        symbol: str,
        strategies: List[str] = None,
        period: str = '1y',
        interval: str = '1d'
    ) -> Dict[str, Any]:
        """
        Compare multiple strategies on the same symbol.
        
        Args:
            symbol: Stock symbol
            strategies: List of strategy names (default: all 4 strategies)
            period: Historical period
            interval: Data interval
            
        Returns:
            Dictionary with comparison results
            
        **Validates: Requirements 5.9**
        """
        if strategies is None:
            strategies = ['rsi', 'macd', 'ema_cross', 'combo']
        
        logger.info(f"Comparing {len(strategies)} strategies for {symbol}")
        
        results = {}
        for strategy in strategies:
            result = self.run_backtest(symbol, strategy, period, interval)
            results[strategy] = result
        
        # Create comparison DataFrame
        comparison_data = []
        for strategy, result in results.items():
            if 'error' not in result:
                metrics = result['metrics']
                comparison_data.append({
                    'strategy': strategy,
                    'final_value': result['final_value'],
                    'total_return_%': metrics['total_return_percent'],
                    'sharpe_ratio': metrics['sharpe_ratio'],
                    'max_drawdown_%': metrics['max_drawdown_percent'],
                    'win_rate_%': metrics['win_rate'],
                    'profit_factor': metrics['profit_factor'],
                    'total_trades': metrics['total_trades']
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        return {
            'symbol': symbol,
            'period': period,
            'strategies': results,
            'comparison': comparison_df.to_dict('records') if not comparison_df.empty else []
        }
