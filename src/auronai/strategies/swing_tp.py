"""
Swing strategy with Take Profit and Time Exit (no Stop Loss).

This strategy replicates the original SwingNoSLStrategy logic:
- Market regime filter using benchmark EMA200 + slope + ADX
- Risk budget dinámico (20% normal, 5% defensivo)
- Drawdown kill switch (5%, 8%, 10% thresholds)
- Only exits on Take Profit (5%) or Time Exit (holding_days)
- NO Stop Loss (by design, to avoid daily data imprecision)
- Tracks individual trades with entry/exit/reason
- Selection by relative strength (no EMA/RSI filters in original)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import pandas as pd
import numpy as np

from auronai.strategies.base_strategy import (
    BaseStrategy,
    MarketRegime,
    StrategyParams
)
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OpenPosition:
    """Track an open position with entry details."""
    symbol: str
    entry_date: datetime
    entry_price: float
    shares: float
    tp_price: float  # Take profit target


class SwingTPStrategy(BaseStrategy):
    """
    Swing strategy with Take Profit and Time Exit (Original Logic).
    
    Features (from original SwingNoSLStrategy):
    - Market regime: benchmark EMA200 + slope + ADX >= 15
    - Risk budget: 20% normal, 5% defensive (based on regime)
    - Drawdown kill switch: 5%, 8%, 10% thresholds with cooldown
    - Selection: Top K by relative strength (20-day lookback)
    - Exit: TP (5%) or Time Exit (holding_days)
    - NO Stop Loss (by design)
    - NO EMA/RSI filters (original uses only relative strength)
    
    **Validates: Requirements FR-7**
    """
    
    def __init__(self, params: StrategyParams):
        """Initialize strategy with parameters."""
        super().__init__(params)
        self.open_positions: Dict[str, OpenPosition] = {}
        self.last_rebalance_date: Optional[datetime] = None
        
        # Drawdown tracking
        self.peak_equity: float = params.risk_budget  # Will be set by backtest
        self.current_equity: float = params.risk_budget
        self.cooldown_until: Optional[datetime] = None
        
        # Drawdown thresholds
        self.dd_threshold_1 = 0.05  # 5%
        self.dd_threshold_2 = 0.08  # 8%
        self.dd_threshold_3 = 0.10  # 10%
        self.cooldown_days = 10
    
    @property
    def name(self) -> str:
        """Strategy name for display."""
        return "Swing TP (Original)"
    
    @property
    def description(self) -> str:
        """Strategy description for UI."""
        return "Original swing strategy: EMA200+ADX regime, dynamic risk, TP+TimeExit (no SL)"
    
    def _calculate_market_regime_advanced(
        self,
        benchmark_features: pd.DataFrame,
        current_idx: int
    ) -> bool:
        """
        Calculate market regime using benchmark (original logic).
        
        Uses:
        - EMA200: Close > EMA200
        - Slope: EMA200 slope over 20 days > 0
        - ADX: >= 15
        
        Returns True if market is favorable (bull regime).
        """
        if current_idx < 200:
            return False
        
        try:
            # Check Close > EMA200
            close = benchmark_features['Close'].iloc[current_idx]
            ema200 = benchmark_features['ema_200'].iloc[current_idx]
            
            if pd.isna(close) or pd.isna(ema200):
                return False
            
            close_above_ema = close > ema200
            
            # Check EMA200 slope
            if current_idx < 220:
                slope_positive = False
            else:
                ema200_20_ago = benchmark_features['ema_200'].iloc[current_idx - 20]
                if pd.isna(ema200_20_ago):
                    slope_positive = False
                else:
                    slope = ema200 - ema200_20_ago
                    slope_positive = slope > 0
            
            # Check ADX >= 15
            if 'adx' in benchmark_features.columns:
                adx_value = benchmark_features['adx'].iloc[current_idx]
                adx_ok = not pd.isna(adx_value) and adx_value >= 15
            else:
                # If ADX not available, log warning and assume OK
                logger.warning("ADX not available in features, assuming regime OK")
                adx_ok = True
            
            market_ok = close_above_ema and slope_positive and adx_ok
            
            if current_idx % 50 == 0:  # Log every 50 days
                logger.debug(
                    f"Advanced regime at idx {current_idx}: {market_ok} "
                    f"(close>{ema200}: {close_above_ema}, slope>0: {slope_positive}, "
                    f"adx>=15: {adx_ok})"
                )
            
            return market_ok
            
        except (KeyError, IndexError) as e:
            logger.warning(f"Error calculating advanced regime: {e}")
            return False
    
    def _calculate_risk_budget_dynamic(
        self,
        market_ok: bool,
        current_date: datetime,
        current_equity: float
    ) -> float:
        """
        Calculate dynamic risk budget based on regime and drawdown.
        
        Logic (from original):
        - If in cooldown: 0%
        - If market OK: 20% (base_risk_budget)
        - If market NOT OK: 5% (defensive_risk_budget)
        - Drawdown adjustments:
          - DD >= 10%: PAUSE (cooldown for 10 days)
          - DD >= 8%: Max 5%
          - DD >= 5%: Max 10%
        """
        # Update equity tracking
        self.current_equity = current_equity
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # Check cooldown
        if self.cooldown_until is not None and current_date < self.cooldown_until:
            logger.info(f"In cooldown until {self.cooldown_until}")
            return 0.0
        
        # Base risk budget
        if market_ok:
            risk_budget = self.params.risk_budget  # 20%
        else:
            risk_budget = self.params.defensive_risk_budget  # 5%
        
        # Calculate drawdown
        dd = (self.peak_equity - current_equity) / self.peak_equity if self.peak_equity > 0 else 0
        
        # Apply drawdown kill switch
        if dd >= self.dd_threshold_3:  # 10%
            logger.warning(
                f"Drawdown {dd:.2%} >= {self.dd_threshold_3:.2%}: "
                f"PAUSING for {self.cooldown_days} days"
            )
            self.cooldown_until = current_date + timedelta(days=self.cooldown_days)
            return 0.0
        elif dd >= self.dd_threshold_2:  # 8%
            risk_budget = min(risk_budget, 0.05)
            logger.info(f"Drawdown {dd:.2%}: reducing risk to 5%")
        elif dd >= self.dd_threshold_1:  # 5%
            risk_budget = min(risk_budget, 0.10)
            logger.info(f"Drawdown {dd:.2%}: reducing risk to 10%")
        
        return risk_budget
    
    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime
    ) -> Dict[str, float]:
        """
        Generate trading signals (original logic).
        
        Selection:
        - Top K by relative strength (20-day lookback vs benchmark)
        - NO EMA/RSI filters (original doesn't use them)
        - Tries to fill portfolio EVERY day (not just on rebalance days)
        
        Args:
            features: DataFrame with OHLCV + indicators for all symbols
            regime: Current market regime (from RegimeEngine)
            current_date: Current simulation date
        
        Returns:
            Dictionary mapping symbol -> relative strength score
        """
        # Only trade in bull regime
        if regime != MarketRegime.BULL:
            logger.debug(f"Skipping signals - regime is {regime.value}, need BULL")
            return {}
        
        # Calculate how many positions we can open
        # (top_k minus currently open positions)
        available_slots = self.params.top_k - len(self.open_positions)
        
        if available_slots <= 0:
            logger.debug(f"Portfolio full ({len(self.open_positions)}/{self.params.top_k}), no new signals")
            return {}
        
        # Select by relative strength ONLY (no EMA/RSI filters in original)
        try:
            candidates = features[
                ~features['relative_strength'].isna()
            ].copy()
            
            if len(candidates) == 0:
                logger.debug("No candidates with relative strength data")
                return {}
            
            # Filter out symbols we already hold
            open_symbols = set(self.open_positions.keys())
            candidates = candidates[~candidates.index.isin(open_symbols)]
            
            if len(candidates) == 0:
                logger.debug("No new candidates (all already held)")
                return {}
            
            # Sort by relative strength (descending)
            candidates = candidates.sort_values('relative_strength', ascending=False)
            
            # Select top available_slots
            selected = candidates.head(available_slots)
            
            # Return relative strength scores
            signals = {
                symbol: row['relative_strength']
                for symbol, row in selected.iterrows()
            }
            
            logger.info(
                f"Generated {len(signals)} swing TP signals (by RS only): "
                f"{list(signals.keys())} (portfolio: {len(self.open_positions)}/{self.params.top_k})"
            )
            
            return signals
            
        except KeyError as e:
            logger.error(f"Missing required column in features: {e}")
            return {}
    
    def _check_exits_with_data(
        self,
        features: pd.DataFrame,
        current_date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """
        Check if any open positions should exit and return exit details.
        
        Exit conditions:
        1. High >= TP price (Take Profit hit) - exit at TP price
        2. Days held >= holding_days (Time Exit) - exit at Close price
        
        Returns:
            Dictionary mapping symbol -> exit details {'exit_price': float, 'reason': str}
        """
        exit_info = {}
        
        logger.debug(f"Checking exits for {len(self.open_positions)} positions on {current_date.date()}")
        
        for symbol, position in list(self.open_positions.items()):
            # Check if symbol has data
            if symbol not in features.index:
                logger.debug(f"No data for {symbol}, skipping exit check")
                continue
            
            symbol_data = features.loc[symbol]
            
            # Get prices
            high_val = float(symbol_data['High']) if not isinstance(symbol_data, pd.DataFrame) else float(symbol_data['High'].iloc[0])
            close_val = float(symbol_data['Close']) if not isinstance(symbol_data, pd.DataFrame) else float(symbol_data['Close'].iloc[0])
            
            # Check Take Profit (use High price)
            if high_val >= position.tp_price:
                logger.info(
                    f"TP hit for {symbol}: High={high_val:.2f} >= "
                    f"TP={position.tp_price:.2f}"
                )
                exit_info[symbol] = {
                    'exit_price': position.tp_price,  # Exit at TP price
                    'reason': 'TP'
                }
                del self.open_positions[symbol]
                continue
            
            # Check Time Exit (use Close price)
            days_held = (current_date - position.entry_date).days
            if days_held >= self.params.holding_days:
                logger.info(
                    f"Time exit for {symbol}: held {days_held} days >= "
                    f"{self.params.holding_days}"
                )
                exit_info[symbol] = {
                    'exit_price': close_val,  # Exit at Close price
                    'reason': 'TimeExit'
                }
                del self.open_positions[symbol]
                continue
        
        if exit_info:
            logger.info(f"Closing {len(exit_info)} positions: {list(exit_info.keys())}")
        
        return exit_info
    
    def risk_model(
        self,
        signals: Dict[str, float],
        features: pd.DataFrame,
        current_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Convert signals to position weights with risk management.
        
        This method ADDS new positions (doesn't close existing ones).
        Exits are handled separately by _check_exits().
        
        Args:
            signals: Raw signals from generate_signals()
            features: Current market features
            current_weights: Current portfolio weights (ignored for swing)
        
        Returns:
            Target weights for portfolio
        """
        if not signals:
            # Return weights for open positions only
            return self._get_position_weights()
        
        # ADD new positions (don't clear existing ones)
        # Exits are handled by _check_exits() which is called daily
        
        # Get current date from features (use first symbol's date)
        current_date = datetime.now()  # Default fallback
        
        # Open new positions
        for symbol in signals:
            # Skip if we already have this position
            if symbol in self.open_positions:
                continue
            
            if symbol not in features.index:
                continue
            
            symbol_data = features.loc[symbol]
            
            # Get entry price (Close of current day)
            if 'Close' not in symbol_data:
                continue
            
            entry_price = float(symbol_data['Close']) if not isinstance(symbol_data, pd.DataFrame) else float(symbol_data['Close'].iloc[0])
            
            # Calculate TP price
            tp_price = entry_price * self.params.tp_multiplier
            
            # Create position
            position = OpenPosition(
                symbol=symbol,
                entry_date=current_date,  # Will be updated by set_entry_date()
                entry_price=entry_price,
                shares=0.0,  # Will be calculated by backtest runner
                tp_price=tp_price
            )
            
            self.open_positions[symbol] = position
            
            logger.info(
                f"Opening {symbol}: entry=${entry_price:.2f}, "
                f"TP=${tp_price:.2f} (+{(self.params.tp_multiplier-1)*100:.1f}%)"
            )
        
        # Calculate target weights
        return self._get_position_weights()
    
    def set_entry_date(self, date: datetime) -> None:
        """
        Set entry date for all open positions.
        
        This is called by the backtest runner after positions are opened.
        
        Args:
            date: Entry date for positions
        """
        for position in self.open_positions.values():
            position.entry_date = date
    
    def _get_position_weights(self) -> Dict[str, float]:
        """Calculate equal weights for open positions."""
        if not self.open_positions:
            return {}
        
        # Equal weight distribution
        weight = self.params.risk_budget / len(self.open_positions)
        
        # Cap individual positions
        max_position = self.params.risk_budget / self.params.top_k
        weight = min(weight, max_position)
        
        weights = {symbol: weight for symbol in self.open_positions}
        
        return weights
    
    def get_params(self) -> Dict[str, Any]:
        """Return strategy parameters as dictionary."""
        return {
            'top_k': self.params.top_k,
            'holding_days': self.params.holding_days,
            'tp_multiplier': self.params.tp_multiplier,
            'risk_budget': self.params.risk_budget,
            'defensive_risk_budget': self.params.defensive_risk_budget,
            'exit_rules': 'TP + Time Exit (NO SL)'
        }
