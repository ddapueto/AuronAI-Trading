"""
Base strategy interface for trading strategies.

This module defines the abstract base class that all trading strategies
must implement, along with supporting data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any

import pandas as pd


class MarketRegime(Enum):
    """Market regime states for regime-aware trading."""
    
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"
    
    def __str__(self) -> str:
        return self.value


@dataclass
class StrategyParams:
    """
    Base parameters for all trading strategies.
    
    Attributes:
        top_k: Number of top symbols to select
        holding_days: Target holding period in days
        tp_multiplier: Take profit multiplier (e.g., 1.05 = 5% profit target)
        risk_budget: Maximum portfolio risk allocation (0.0 to 1.0)
        defensive_risk_budget: Risk budget for defensive/neutral regimes
    """
    
    top_k: int = 3
    holding_days: int = 10
    tp_multiplier: float = 1.05
    risk_budget: float = 0.20
    defensive_risk_budget: float = 0.05
    
    def __post_init__(self):
        """Validate parameters."""
        if self.top_k < 1:
            raise ValueError("top_k must be >= 1")
        if self.holding_days < 1:
            raise ValueError("holding_days must be >= 1")
        if self.tp_multiplier <= 1.0:
            raise ValueError("tp_multiplier must be > 1.0")
        if not 0.0 < self.risk_budget <= 1.0:
            raise ValueError("risk_budget must be between 0.0 and 1.0")
        if not 0.0 < self.defensive_risk_budget <= 1.0:
            raise ValueError("defensive_risk_budget must be between 0.0 and 1.0")


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    
    All strategies must implement:
    1. generate_signals() - Return target weights per symbol
    2. risk_model() - Apply risk constraints to weights
    3. get_params() - Return strategy parameters
    4. name - Strategy name property
    5. description - Strategy description property
    
    Strategies can optionally filter by market regime to only trade
    in favorable conditions (e.g., long-only in BULL markets).
    """
    
    def __init__(self, params: StrategyParams):
        """
        Initialize strategy with parameters.
        
        Args:
            params: Strategy parameters
        """
        self.params = params
    
    @abstractmethod
    def generate_signals(
        self,
        features: pd.DataFrame,
        regime: MarketRegime,
        current_date: datetime
    ) -> Dict[str, float]:
        """
        Generate trading signals for all symbols.
        
        This method analyzes market features and returns target portfolio
        weights for each symbol. Weights should sum to <= 1.0.
        
        Args:
            features: DataFrame with OHLCV + indicators for all symbols
                     Index: datetime
                     Columns: symbol, open, high, low, close, volume,
                             ema_20, ema_50, ema_200, rsi, macd, etc.
            regime: Current market regime (BULL/BEAR/NEUTRAL)
            current_date: Current simulation date
        
        Returns:
            Dictionary mapping symbol -> target weight (0.0 to 1.0)
            Empty dict if no signals in current regime.
            
        Example:
            {
                'AAPL': 0.33,
                'MSFT': 0.33,
                'GOOGL': 0.34
            }
        
        **Validates: Requirements FR-5, FR-6**
        """
        pass
    
    @abstractmethod
    def risk_model(
        self,
        target_weights: Dict[str, float],
        features: pd.DataFrame,
        current_portfolio: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Apply risk constraints to target weights.
        
        This method adjusts raw signals to respect risk limits:
        - Maximum position size per symbol
        - Maximum total portfolio exposure
        - Correlation constraints (optional)
        - Volatility adjustments (optional)
        
        Args:
            target_weights: Raw weights from generate_signals()
            features: Current market features
            current_portfolio: Current positions {symbol: weight}
        
        Returns:
            Adjusted weights after risk constraints
            
        **Validates: Requirements FR-8**
        """
        pass
    
    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """
        Return strategy parameters as dictionary.
        
        Returns:
            Dictionary with all strategy parameters
            
        Example:
            {
                'top_k': 3,
                'holding_days': 10,
                'tp_multiplier': 1.05,
                'risk_budget': 0.20
            }
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Strategy name for display.
        
        Returns:
            Short strategy name (e.g., "Long Momentum")
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Strategy description for UI.
        
        Returns:
            Detailed strategy description
        """
        pass
