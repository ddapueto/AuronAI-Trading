"""Market data provider using yfinance for real market data.

This module provides real-time and historical market data retrieval with
caching and retry logic for reliability.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import yfinance as yf
from dataclasses import dataclass

from auronai.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with data and expiration time."""
    data: pd.DataFrame
    expires_at: datetime


class MarketDataProvider:
    """Provide market data from Yahoo Finance with caching and retry logic."""
    
    def __init__(
        self,
        cache_ttl_seconds: int = 60,
        max_retries: int = 3,
        retry_delays: List[float] = None
    ):
        """Initialize market data provider.
        
        Args:
            cache_ttl_seconds: Time-to-live for cached data in seconds
            max_retries: Maximum number of retry attempts
            retry_delays: List of delays between retries (default: [1, 2, 4])
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_retries = max_retries
        self.retry_delays = retry_delays or [1.0, 2.0, 4.0]
        self._cache: Dict[str, CacheEntry] = {}
        
        logger.info(
            f"MarketDataProvider initialized with cache_ttl={cache_ttl_seconds}s, "
            f"max_retries={max_retries}"
        )
    
    def _get_cache_key(self, symbol: str, period: str, interval: str) -> str:
        """Generate cache key from parameters.
        
        Args:
            symbol: Stock symbol
            period: Time period
            interval: Data interval
            
        Returns:
            Cache key string
        """
        return f"{symbol}:{period}:{interval}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Get data from cache if not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached DataFrame or None if expired/missing
            
        **Validates: Requirements 2.8**
        """
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if datetime.now() < entry.expires_at:
                logger.debug(f"Cache hit for {cache_key}")
                return entry.data.copy()
            else:
                logger.debug(f"Cache expired for {cache_key}")
                del self._cache[cache_key]
        
        logger.debug(f"Cache miss for {cache_key}")
        return None
    
    def _save_to_cache(self, cache_key: str, data: pd.DataFrame) -> None:
        """Save data to cache with expiration.
        
        Args:
            cache_key: Cache key
            data: DataFrame to cache
            
        **Validates: Requirements 2.8**
        """
        expires_at = datetime.now() + timedelta(seconds=self.cache_ttl_seconds)
        self._cache[cache_key] = CacheEntry(data=data.copy(), expires_at=expires_at)
        logger.debug(f"Cached data for {cache_key} until {expires_at}")
    
    def _validate_data(self, data: pd.DataFrame, symbol: str) -> bool:
        """Validate market data completeness and correctness.
        
        Args:
            data: DataFrame to validate
            symbol: Stock symbol for logging
            
        Returns:
            True if data is valid
            
        **Validates: Requirements 2.5**
        """
        if data is None or data.empty:
            logger.warning(f"No data retrieved for {symbol}")
            return False
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            logger.error(f"Missing columns for {symbol}: {missing_columns}")
            return False
        
        # Check for NaN values
        nan_counts = data[required_columns].isna().sum()
        if nan_counts.any():
            logger.warning(f"NaN values found in {symbol}: {nan_counts[nan_counts > 0].to_dict()}")
            # Allow some NaN but not all
            if nan_counts.sum() > len(data) * 0.5:
                logger.error(f"Too many NaN values in {symbol}")
                return False
        
        # Validate OHLC relationships
        invalid_rows = 0
        for idx in range(len(data)):
            row = data.iloc[idx]
            if pd.notna(row['High']) and pd.notna(row['Low']):
                if row['High'] < max(row['Open'], row['Close']):
                    invalid_rows += 1
                if row['Low'] > min(row['Open'], row['Close']):
                    invalid_rows += 1
        
        if invalid_rows > 0:
            logger.warning(f"Found {invalid_rows} rows with invalid OHLC relationships in {symbol}")
        
        logger.info(f"Data validation passed for {symbol}: {len(data)} rows")
        return True
    
    def _fetch_with_retry(
        self,
        symbol: str,
        period: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Fetch data with retry logic and exponential backoff.
        
        Args:
            symbol: Stock symbol
            period: Time period (e.g., '1mo', '3mo', '1y')
            interval: Data interval (e.g., '1d', '1h')
            
        Returns:
            DataFrame with market data or None if all retries failed
            
        **Validates: Requirements 11.1, 11.2**
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching {symbol} (attempt {attempt + 1}/{self.max_retries})")
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval=interval)
                
                if self._validate_data(data, symbol):
                    # Normalize timezone to avoid comparison issues
                    # yfinance may return tz-aware or tz-naive depending on symbol
                    if hasattr(data.index, 'tz') and data.index.tz is not None:
                        data.index = data.index.tz_localize(None)
                    
                    logger.info(f"Successfully fetched {symbol}: {len(data)} rows")
                    return data
                else:
                    logger.warning(f"Data validation failed for {symbol}")
                    
            except Exception as e:
                logger.warning(
                    f"Error fetching {symbol} (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                # If not last attempt, wait before retry
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.debug(f"Waiting {delay}s before retry...")
                    time.sleep(delay)
        
        logger.error(f"Failed to fetch {symbol} after {self.max_retries} attempts")
        return None
    
    def get_historical_data(
        self,
        symbol: str,
        period: str = '1mo',
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """Get historical market data for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            period: Time period - valid values:
                    1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval: Data interval - valid values:
                      1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
                      
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
            Returns None if data cannot be retrieved
            
        **Validates: Requirements 2.1, 2.2**
        """
        # Check cache first
        cache_key = self._get_cache_key(symbol, period, interval)
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Fetch with retry
        data = self._fetch_with_retry(symbol, period, interval)
        
        if data is not None:
            # Save to cache
            self._save_to_cache(cache_key, data)
            return data
        
        return None
    
    def get_historical_data_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """Get historical market data for a symbol within a date range.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date (datetime object)
            end_date: End date (datetime object)
            interval: Data interval - valid values:
                      1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
                      
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
            Returns None if data cannot be retrieved
        """
        # Convert datetime to string format for yfinance
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Create cache key
        cache_key = f"{symbol}:{start_str}:{end_str}:{interval}"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Fetch with retry using date range
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Fetching {symbol} from {start_str} to {end_str} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_str, end=end_str, interval=interval)
                
                if self._validate_data(data, symbol):
                    # Normalize timezone to avoid comparison issues
                    # yfinance may return tz-aware or tz-naive depending on symbol
                    if hasattr(data.index, 'tz') and data.index.tz is not None:
                        data.index = data.index.tz_localize(None)
                    
                    logger.info(
                        f"Successfully fetched {symbol}: {len(data)} rows "
                        f"({start_str} to {end_str})"
                    )
                    # Save to cache
                    self._save_to_cache(cache_key, data)
                    return data
                else:
                    logger.warning(f"Data validation failed for {symbol}")
                    
            except Exception as e:
                logger.warning(
                    f"Error fetching {symbol} (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                # If not last attempt, wait before retry
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.debug(f"Waiting {delay}s before retry...")
                    time.sleep(delay)
        
        logger.error(f"Failed to fetch {symbol} after {self.max_retries} attempts")
        return None
    
    def get_current_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price and volume data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with current market data:
            {
                'symbol': str,
                'price': float,
                'open': float,
                'high': float,
                'low': float,
                'volume': int,
                'timestamp': datetime
            }
            Returns None if data cannot be retrieved
            
        **Validates: Requirements 2.1**
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get latest price data
            hist = ticker.history(period='1d', interval='1m')
            
            if hist.empty:
                logger.warning(f"No current data available for {symbol}")
                return None
            
            latest = hist.iloc[-1]
            
            result = {
                'symbol': symbol,
                'price': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']),
                'timestamp': latest.name.to_pydatetime()
            }
            
            logger.info(f"Current data for {symbol}: ${result['price']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting current data for {symbol}: {e}")
            return None
    
    def get_multiple_symbols(
        self,
        symbols: List[str],
        period: str = '1mo',
        interval: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            period: Time period
            interval: Data interval
            
        Returns:
            Dictionary mapping symbols to DataFrames
            Symbols that fail to retrieve will not be in the result
            
        **Validates: Requirements 2.3**
        """
        results = {}
        
        logger.info(f"Fetching data for {len(symbols)} symbols")
        
        for symbol in symbols:
            data = self.get_historical_data(symbol, period, interval)
            if data is not None:
                results[symbol] = data
            else:
                logger.warning(f"Skipping {symbol} due to fetch failure")
        
        logger.info(f"Successfully fetched {len(results)}/{len(symbols)} symbols")
        return results
    
    def validate_symbol(self, symbol: str) -> bool:
        """Check if a symbol exists and is tradeable.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if symbol is valid and tradeable
            
        **Validates: Requirements 2.6**
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got valid info
            if not info or 'symbol' not in info:
                logger.warning(f"Symbol {symbol} not found")
                return False
            
            # Try to get some recent data
            hist = ticker.history(period='5d')
            if hist.empty:
                logger.warning(f"Symbol {symbol} has no recent data")
                return False
            
            logger.info(f"Symbol {symbol} validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        now = datetime.now()
        active_entries = sum(1 for entry in self._cache.values() if entry.expires_at > now)
        
        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': len(self._cache) - active_entries
        }
