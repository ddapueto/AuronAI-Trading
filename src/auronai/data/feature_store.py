"""
Feature store for caching precomputed technical indicators.

This module provides caching of technical indicators to avoid redundant
calculations during backtesting.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from auronai.indicators.technical_indicators import TechnicalIndicators


class FeatureStore:
    """
    Precomputes and caches technical indicators.
    
    Directory structure:
        data/cache/features/
            ├── AAPL/
            │   ├── 2023.parquet
            │   └── 2024.parquet
            └── metadata.json
    
    Features:
    - Caches all technical indicators
    - Calculates relative strength vs benchmark
    - Year-based partitioning
    - Automatic invalidation
    """
    
    def __init__(
        self,
        cache_dir: str = "data/cache",
        indicators: Optional[TechnicalIndicators] = None
    ):
        """
        Initialize FeatureStore.
        
        Args:
            cache_dir: Root directory for cache storage
            indicators: TechnicalIndicators instance (creates new if None)
        """
        self.cache_dir = Path(cache_dir)
        self.features_dir = self.cache_dir / "features"
        self.indicators = indicators or TechnicalIndicators()
        
        # Create directories
        self.features_dir.mkdir(parents=True, exist_ok=True)
    
    def get_features(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Get precomputed features from cache.
        
        Args:
            symbol: Stock symbol
            start_date: Start date for data range
            end_date: End date for data range
        
        Returns:
            DataFrame with OHLCV + indicators, or None if not cached
            
        Columns include:
        - OHLCV: Open, High, Low, Close, Volume
        - EMAs: ema_20, ema_50, ema_200
        - MACD: macd, macd_signal, macd_hist
        - RSI: rsi
        - Stochastic: stochastic_k, stochastic_d
        - Volatility: atr, bb_upper, bb_middle, bb_lower
        - Trend: adx
        - Strength: relative_strength
        """
        symbol_dir = self.features_dir / symbol
        
        if not symbol_dir.exists():
            return None
        
        # Determine which year files we need
        start_year = start_date.year
        end_year = end_date.year
        
        # Collect data from all relevant year files
        dfs = []
        for year in range(start_year, end_year + 1):
            year_file = symbol_dir / f"{year}.parquet"
            
            if not year_file.exists():
                return None
            
            try:
                df = pd.read_parquet(year_file)
                dfs.append(df)
            except Exception:
                return None
        
        if not dfs:
            return None
        
        # Combine all years
        combined_df = pd.concat(dfs, ignore_index=False)
        
        # Filter to requested date range
        combined_df = combined_df[
            (combined_df.index >= start_date) &
            (combined_df.index <= end_date)
        ]
        
        if combined_df.empty:
            return None
        
        return combined_df
    
    def compute_and_save(
        self,
        symbol: str,
        ohlcv_data: pd.DataFrame,
        benchmark_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Compute all features and save to Parquet.
        
        Args:
            symbol: Stock symbol
            ohlcv_data: DataFrame with OHLCV data
            benchmark_data: Optional benchmark data for relative strength
        
        Returns:
            DataFrame with all computed features
        """
        # Start with OHLCV data
        features = ohlcv_data.copy()
        
        # Calculate EMAs
        features['ema_20'] = self.indicators.calculate_ema(features, period=20)
        features['ema_50'] = self.indicators.calculate_ema(features, period=50)
        features['ema_200'] = self.indicators.calculate_ema(features, period=200)
        
        # Calculate MACD
        macd_data = self.indicators.calculate_macd(features)
        if macd_data:
            features['macd'] = macd_data['macd']
            features['macd_signal'] = macd_data['signal']
            features['macd_hist'] = macd_data['histogram']
        else:
            features['macd'] = None
            features['macd_signal'] = None
            features['macd_hist'] = None
        
        # Calculate RSI
        features['rsi'] = self.indicators.calculate_rsi(features)
        
        # Calculate Stochastic
        stoch_data = self.indicators.calculate_stochastic(features)
        if stoch_data:
            features['stochastic_k'] = stoch_data['k']
            features['stochastic_d'] = stoch_data['d']
        else:
            features['stochastic_k'] = 50.0  # Neutral value
            features['stochastic_d'] = 50.0
        
        # Calculate ATR
        features['atr'] = self.indicators.calculate_atr(features)
        
        # Calculate Bollinger Bands
        bb_data = self.indicators.calculate_bollinger_bands(features)
        if bb_data:
            features['bb_upper'] = bb_data['upper']
            features['bb_middle'] = bb_data['middle']
            features['bb_lower'] = bb_data['lower']
        else:
            features['bb_upper'] = None
            features['bb_middle'] = None
            features['bb_lower'] = None
        
        # Calculate ADX (for regime detection)
        features['adx'] = self.indicators.calculate_adx(features)
        
        # Calculate relative strength vs benchmark
        if benchmark_data is not None:
            features['relative_strength'] = self._calculate_relative_strength(
                features, benchmark_data
            )
        else:
            features['relative_strength'] = 0.0
        
        # Save to Parquet partitioned by year
        symbol_dir = self.features_dir / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract year from index (handle both DatetimeIndex and regular Index)
        if hasattr(features.index, 'year'):
            # DatetimeIndex
            years = features.index.year
        else:
            # Regular Index with datetime values
            years = pd.DatetimeIndex(features.index).year
        
        for year, year_data in features.groupby(years):
            year_file = symbol_dir / f"{year}.parquet"
            year_data.to_parquet(year_file, compression='snappy')
        
        return features
    
    def invalidate(self, symbol: str) -> None:
        """
        Invalidate cached features for symbol.
        
        Args:
            symbol: Stock symbol to invalidate
        """
        symbol_dir = self.features_dir / symbol
        
        if symbol_dir.exists():
            for file in symbol_dir.glob("*.parquet"):
                file.unlink()
            symbol_dir.rmdir()
    
    def _calculate_relative_strength(
        self,
        symbol_data: pd.DataFrame,
        benchmark_data: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate relative strength vs benchmark.
        
        Relative strength = (symbol_return - benchmark_return) over 20 days
        
        Args:
            symbol_data: DataFrame with symbol OHLCV
            benchmark_data: DataFrame with benchmark OHLCV
        
        Returns:
            Series with relative strength values
        """
        # Calculate 20-day returns
        symbol_returns = symbol_data['Close'].pct_change(20)
        benchmark_returns = benchmark_data['Close'].pct_change(20)
        
        # Ensure both indices are timezone-naive BEFORE creating DataFrame
        # This prevents timezone comparison errors in pandas
        if hasattr(symbol_returns.index, 'tz') and symbol_returns.index.tz is not None:
            symbol_returns = symbol_returns.copy()
            symbol_returns.index = symbol_returns.index.tz_localize(None)
        
        if hasattr(benchmark_returns.index, 'tz') and benchmark_returns.index.tz is not None:
            benchmark_returns = benchmark_returns.copy()
            benchmark_returns.index = benchmark_returns.index.tz_localize(None)
        
        # Ensure both are Series with clean indices
        symbol_returns = pd.Series(symbol_returns.values, index=symbol_returns.index)
        benchmark_returns = pd.Series(benchmark_returns.values, index=benchmark_returns.index)
        
        # Align indices by reindexing benchmark to symbol's index
        # This avoids pandas trying to merge two potentially mismatched indices
        benchmark_aligned = benchmark_returns.reindex(symbol_returns.index, method='ffill')
        
        # Calculate relative strength
        relative_strength = symbol_returns - benchmark_aligned
        
        return relative_strength.fillna(0.0)
