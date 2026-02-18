"""
Market regime detection engine.

This module provides centralized regime detection using benchmark analysis
to classify market conditions as BULL, BEAR, or NEUTRAL.
"""

from typing import Optional

import pandas as pd

from auronai.strategies.base_strategy import MarketRegime
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


class RegimeEngine:
    """
    Centralized market regime detection using benchmark (QQQ).
    
    Regime Rules:
    - BULL: Close > EMA200 AND EMA200 slope > 0
    - BEAR: Close < EMA200 AND EMA200 slope < 0
    - NEUTRAL: Otherwise (choppy/sideways market)
    
    Note: Original design included ADX, but TechnicalIndicators doesn't
    implement it yet. Using simplified rules for MVP.
    """
    
    def __init__(
        self,
        benchmark: str = 'QQQ',
        ema_period: int = 200,
        slope_lookback: int = 20
    ):
        """
        Initialize regime engine.
        
        Args:
            benchmark: Benchmark symbol for regime detection (default: QQQ)
            ema_period: EMA period for trend detection (default: 200)
            slope_lookback: Lookback period for EMA slope calculation (default: 20)
        """
        self.benchmark = benchmark
        self.ema_period = ema_period
        self.slope_lookback = slope_lookback
        
        logger.info(
            f"RegimeEngine initialized: benchmark={benchmark}, "
            f"ema_period={ema_period}, slope_lookback={slope_lookback}"
        )
    
    def detect_regime(
        self,
        benchmark_data: pd.DataFrame,
        current_idx: int
    ) -> MarketRegime:
        """
        Detect current market regime.
        
        Args:
            benchmark_data: DataFrame with OHLCV + indicators for benchmark
                           Must include 'Close' and 'ema_200' columns
            current_idx: Current index in data (integer position)
        
        Returns:
            MarketRegime enum (BULL/BEAR/NEUTRAL)
            
        **Validates: Requirements FR-6**
        """
        # Need enough data for EMA calculation
        if current_idx < self.ema_period:
            logger.debug(f"Insufficient data at idx {current_idx}, returning NEUTRAL")
            return MarketRegime.NEUTRAL
        
        try:
            # Get current values
            close = benchmark_data['Close'].iloc[current_idx]
            ema200 = benchmark_data['ema_200'].iloc[current_idx]
            
            # Check if EMA is valid (not NaN)
            if pd.isna(ema200):
                logger.debug(f"EMA200 is NaN at idx {current_idx}, returning NEUTRAL")
                return MarketRegime.NEUTRAL
            
            # Calculate EMA slope
            slope = 0.0
            if current_idx >= self.ema_period + self.slope_lookback:
                ema_prev = benchmark_data['ema_200'].iloc[current_idx - self.slope_lookback]
                if not pd.isna(ema_prev):
                    slope = ema200 - ema_prev
            
            # Determine regime
            close_above_ema = close > ema200
            slope_positive = slope > 0
            
            if close_above_ema and slope_positive:
                regime = MarketRegime.BULL
            elif not close_above_ema and not slope_positive:
                regime = MarketRegime.BEAR
            else:
                regime = MarketRegime.NEUTRAL
            
            logger.debug(
                f"Regime at idx {current_idx}: {regime.value} "
                f"(close={close:.2f}, ema200={ema200:.2f}, slope={slope:.4f})"
            )
            
            return regime
            
        except (KeyError, IndexError) as e:
            logger.error(f"Error detecting regime at idx {current_idx}: {e}")
            return MarketRegime.NEUTRAL
    
    def get_regime_history(
        self,
        benchmark_data: pd.DataFrame
    ) -> pd.Series:
        """
        Get regime for all dates in benchmark data.
        
        Args:
            benchmark_data: DataFrame with OHLCV + indicators for benchmark
        
        Returns:
            Series with regime for each date (index matches benchmark_data)
            
        **Validates: Requirements FR-6**
        """
        logger.info(f"Calculating regime history for {len(benchmark_data)} periods")
        
        regimes = []
        for i in range(len(benchmark_data)):
            regime = self.detect_regime(benchmark_data, i)
            regimes.append(regime.value)
        
        regime_series = pd.Series(regimes, index=benchmark_data.index)
        
        # Log regime distribution
        regime_counts = regime_series.value_counts()
        logger.info(f"Regime distribution: {regime_counts.to_dict()}")
        
        return regime_series
    
    def get_current_regime(
        self,
        benchmark_data: pd.DataFrame
    ) -> MarketRegime:
        """
        Get regime for the most recent date in benchmark data.
        
        Args:
            benchmark_data: DataFrame with OHLCV + indicators for benchmark
        
        Returns:
            Current MarketRegime
        """
        if len(benchmark_data) == 0:
            logger.warning("Empty benchmark data, returning NEUTRAL")
            return MarketRegime.NEUTRAL
        
        return self.detect_regime(benchmark_data, len(benchmark_data) - 1)
