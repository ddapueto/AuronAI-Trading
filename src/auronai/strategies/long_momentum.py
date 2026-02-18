"""
Long-only momentum strategy for bull markets.

This strategy selects top momentum stocks based on relative strength
and only trades during BULL market regimes.
"""

from datetime import datetime
from typing import Dict, Any
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


class LongMomentumStrategy(BaseStrategy):
    """
    Long-only momentum strategy for BULL regime.
    
    Selection Criteria:
    - Top K symbols by relative strength (vs benchmark)
    - Positive EMA trend (EMA20 > EMA50)
    - RSI not overbought (< 70)
    
    Exit Rules:
    - Take profit: +5% (configurable via tp_multiplier)
    - Time exit: 10 days (configurable via holding_days)
    - Trend reversal: EMA20 crosses below EMA50
    
    **Validates: Requirements FR-7**
    """
    
    def __init__(self, params: StrategyParams):
        """Initialize strategy with parameters."""
        super().__init__(params)
        self.open_positions: Dict[str, OpenPosition] = {}
    
    @property
    def name(self) -> str:
        """Strategy name for display."""
        return "Long Momentum"
    
    @property
    def description(self) -> str:
        """Strategy description for UI."""
        return "Long-only momentum strategy for bull markets"
    
    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime
    ) -> Dict[str, float]:
        """
        Select top K symbols by relative strength.
        
        Args:
            features: DataFrame with OHLCV + indicators for all symbols
            regime: Current market regime
            current_date: Current simulation date
        
        Returns:
            Dictionary mapping symbol -> target weight
            Empty dict if not in BULL regime
        """
        # Only trade in bull regime
        if regime != MarketRegime.BULL:
            logger.debug(f"Skipping signals - regime is {regime.value}, need BULL")
            return {}
        
        # Calculate how many positions we can open
        available_slots = self.params.top_k - len(self.open_positions)
        
        if available_slots <= 0:
            logger.debug(f"Portfolio full ({len(self.open_positions)}/{self.params.top_k}), no new signals")
            return {}
        
        # Check if required columns exist
        required_cols = ['ema_20', 'ema_50', 'rsi', 'relative_strength']
        missing_cols = [col for col in required_cols if col not in features.columns]
        
        if missing_cols:
            logger.debug(f"Missing required columns: {missing_cols}, skipping signal generation")
            return {}
        
        # Filter: EMA20 > EMA50 and RSI < 70
        try:
            # Check if we have any valid data
            if features.empty:
                logger.debug("Empty features DataFrame")
                return {}
            
            candidates = features[
                (features['ema_20'] > features['ema_50']) &
                (features['rsi'] < 70) &
                (~features['ema_20'].isna()) &
                (~features['ema_50'].isna()) &
                (~features['rsi'].isna()) &
                (~features['relative_strength'].isna())
            ].copy()
            
            if len(candidates) == 0:
                logger.debug("No candidates passed filters")
                return {}
            
            # Filter out symbols we already hold
            open_symbols = set(self.open_positions.keys())
            candidates = candidates[~candidates.index.isin(open_symbols)]
            
            if len(candidates) == 0:
                logger.debug("No new candidates (all already held)")
                return {}
            
            # Sort by relative strength (descending = strongest first)
            candidates = candidates.sort_values('relative_strength', ascending=False)
            
            # Select top available_slots
            selected = candidates.head(available_slots)
            
            # Equal weight distribution
            weight = 1.0 / len(selected) if len(selected) > 0 else 0.0
            
            signals = {symbol: weight for symbol in selected.index}
            
            logger.info(
                f"Generated {len(signals)} long signals: "
                f"{list(signals.keys())} (portfolio: {len(self.open_positions)}/{self.params.top_k})"
            )
            
            return signals
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.debug(f"Error generating signals: {e}")
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
        3. EMA20 < EMA50 (Trend Reversal) - exit at Close price
        
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
            
            # Get prices and indicators
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
            
            # Check Trend Reversal (EMA20 < EMA50)
            if 'ema_20' in symbol_data and 'ema_50' in symbol_data:
                ema20 = float(symbol_data['ema_20']) if not isinstance(symbol_data, pd.DataFrame) else float(symbol_data['ema_20'].iloc[0])
                ema50 = float(symbol_data['ema_50']) if not isinstance(symbol_data, pd.DataFrame) else float(symbol_data['ema_50'].iloc[0])
                
                if not pd.isna(ema20) and not pd.isna(ema50) and ema20 < ema50:
                    logger.info(
                        f"Trend reversal for {symbol}: EMA20={ema20:.2f} < "
                        f"EMA50={ema50:.2f}"
                    )
                    exit_info[symbol] = {
                        'exit_price': close_val,  # Exit at Close price
                        'reason': 'TrendReversal'
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
    
    def set_entry_date(self, date: datetime) -> None:
        """
        Set entry date for all open positions.
        
        This is called by the backtest runner after positions are opened.
        
        Args:
            date: Entry date for positions
        """
        for position in self.open_positions.values():
            position.entry_date = date
    
    def risk_model(
        self,
        target_weights: Dict[str, float],
        features: pd.DataFrame,
        current_portfolio: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Apply risk constraints to target weights and track positions.
        
        Constraints:
        - Maximum total exposure = risk_budget (default 20%)
        - Maximum position size = risk_budget / top_k
        
        Args:
            target_weights: Raw weights from generate_signals()
            features: Current market features
            current_portfolio: Current positions
        
        Returns:
            Adjusted weights after risk constraints
        """
        if not target_weights:
            # Return weights for open positions only
            return self._get_position_weights()
        
        # ADD new positions (don't clear existing ones)
        # Exits are handled by _check_exits_with_data() which is called daily
        
        # Open new positions
        for symbol in target_weights:
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
                entry_date=datetime.now(),  # Will be updated by set_entry_date()
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
            'defensive_risk_budget': self.params.defensive_risk_budget
        }
