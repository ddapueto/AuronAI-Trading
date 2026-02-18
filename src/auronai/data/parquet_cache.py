"""
Parquet-based cache for OHLCV market data.

This module provides persistent caching of market data using Parquet files,
partitioned by symbol and year for efficient storage and retrieval.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from auronai.utils.logger import get_logger

logger = get_logger(__name__)


class ParquetCache:
    """
    Manages market data persistence using Parquet files.
    
    Directory structure:
        data/cache/
            ├── ohlcv/
            │   ├── AAPL/
            │   │   ├── 2020.parquet
            │   │   ├── 2021.parquet
            │   │   └── 2022.parquet
            │   └── MSFT/
            │       └── ...
            └── metadata.json
    
    Features:
    - Year-based partitioning for efficient storage
    - SHA256 hashing for data versioning
    - Automatic directory management
    - Data integrity validation
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize ParquetCache.
        
        Args:
            cache_dir: Root directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.ohlcv_dir = self.cache_dir / "ohlcv"
        self.metadata_file = self.cache_dir / "metadata.json"
        
        # Create directories if they don't exist
        self.ohlcv_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize metadata
        self._metadata = self._load_metadata()
    
    def get_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Get OHLCV data from cache.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date for data range
            end_date: End date for data range
        
        Returns:
            DataFrame with OHLCV data, or None if data not in cache or incomplete
        """
        symbol_dir = self.ohlcv_dir / symbol
        
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
                # Missing data for this year
                return None
            
            try:
                df = pd.read_parquet(year_file)
                dfs.append(df)
            except Exception:
                # Corrupted file
                return None
        
        if not dfs:
            return None
        
        # Combine all years
        combined_df = pd.concat(dfs, ignore_index=False)
        
        # Convert to timezone-naive if needed (for comparison with datetime objects)
        if hasattr(combined_df.index, 'tz') and combined_df.index.tz is not None:
            combined_df.index = combined_df.index.tz_localize(None)
        
        # Filter to requested date range
        combined_df = combined_df[
            (combined_df.index >= start_date) &
            (combined_df.index <= end_date)
        ]
        
        # Validate we have data for the full range
        if combined_df.empty:
            return None
        
        # Check if we have continuous data (no large gaps)
        if not self._validate_data_continuity(combined_df, start_date, end_date):
            return None
        
        return combined_df
    
    def save_data(
        self,
        symbol: str,
        data: pd.DataFrame
    ) -> str:
        """
        Save OHLCV data to Parquet partitioned by year.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            data: DataFrame with OHLCV data (index must be DatetimeIndex)
        
        Returns:
            data_version: SHA256 hash of the data
        
        Raises:
            ValueError: If data is invalid or index is not DatetimeIndex
        """
        if data.empty:
            raise ValueError("Cannot save empty DataFrame")
        
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be DatetimeIndex")
        
        # Convert to timezone-naive for consistency
        if hasattr(data.index, 'tz') and data.index.tz is not None:
            data = data.copy()
            data.index = data.index.tz_localize(None)
        
        # Validate OHLCV columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = set(required_columns) - set(data.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean invalid OHLC relationships instead of failing
        data = self._clean_ohlc_data(data)
        
        # Create symbol directory
        symbol_dir = self.ohlcv_dir / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        
        # Group by year and save
        for year, year_data in data.groupby(data.index.year):
            year_file = symbol_dir / f"{year}.parquet"
            year_data.to_parquet(year_file, compression='snappy')
        
        # Calculate data version (hash)
        data_version = self._calculate_data_hash(data)
        
        # Update metadata
        self._metadata[symbol] = {
            'data_version': data_version,
            'last_updated': datetime.now().isoformat(),
            'start_date': data.index.min().isoformat(),
            'end_date': data.index.max().isoformat(),
            'num_records': len(data)
        }
        self._save_metadata()
        
        return data_version
    
    def get_data_version(self, symbol: str) -> Optional[str]:
        """
        Get SHA256 hash of cached data for versioning.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            SHA256 hash string, or None if symbol not in cache
        """
        if symbol in self._metadata:
            return self._metadata[symbol]['data_version']
        return None
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cache for symbol or all symbols.
        
        Args:
            symbol: Stock symbol to clear, or None to clear all
        """
        if symbol:
            # Clear specific symbol
            symbol_dir = self.ohlcv_dir / symbol
            if symbol_dir.exists():
                for file in symbol_dir.glob("*.parquet"):
                    file.unlink()
                symbol_dir.rmdir()
            
            # Remove from metadata
            if symbol in self._metadata:
                del self._metadata[symbol]
                self._save_metadata()
        else:
            # Clear all
            for symbol_dir in self.ohlcv_dir.iterdir():
                if symbol_dir.is_dir():
                    for file in symbol_dir.glob("*.parquet"):
                        file.unlink()
                    symbol_dir.rmdir()
            
            # Clear metadata
            self._metadata = {}
            self._save_metadata()
    
    def get_cached_symbols(self) -> list[str]:
        """
        Get list of symbols currently in cache.
        
        Returns:
            List of symbol strings
        """
        return list(self._metadata.keys())
    
    def get_cache_info(self, symbol: str) -> Optional[dict]:
        """
        Get cache metadata for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dictionary with cache info, or None if not cached
        """
        return self._metadata.get(symbol)
    
    # Private methods
    
    def _load_metadata(self) -> dict:
        """Load metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_metadata(self) -> None:
        """Save metadata to JSON file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self._metadata, f, indent=2)
    
    def _calculate_data_hash(self, data: pd.DataFrame) -> str:
        """
        Calculate SHA256 hash of DataFrame for versioning.
        
        Args:
            data: DataFrame to hash
        
        Returns:
            SHA256 hash string
        """
        # Convert to bytes for hashing
        # Use sorted columns to ensure consistent ordering
        sorted_cols = sorted(data.columns)
        data_bytes = data[sorted_cols].to_csv(index=True).encode('utf-8')
        
        return hashlib.sha256(data_bytes).hexdigest()
    
    def _validate_ohlc_relationships(self, data: pd.DataFrame) -> bool:
        """
        Validate OHLC relationships (High >= Low, etc.).
        
        Args:
            data: DataFrame with OHLCV data
        
        Returns:
            True if valid, False otherwise
        """
        # High should be >= Low
        if not (data['High'] >= data['Low']).all():
            return False
        
        # High should be >= Open and Close
        if not (data['High'] >= data['Open']).all():
            return False
        if not (data['High'] >= data['Close']).all():
            return False
        
        # Low should be <= Open and Close
        if not (data['Low'] <= data['Open']).all():
            return False
        if not (data['Low'] <= data['Close']).all():
            return False
        
        # Volume should be non-negative
        if not (data['Volume'] >= 0).all():
            return False
        
        return True
    
    def _clean_ohlc_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean OHLC data by fixing invalid relationships.
        
        Yahoo Finance sometimes returns bad data where High < Low or similar.
        This method fixes those issues by adjusting the values.
        
        Args:
            data: DataFrame with OHLCV data
        
        Returns:
            Cleaned DataFrame
        """
        data = data.copy()
        
        # Fix High < Low: set High = max(High, Low)
        invalid_high_low = data['High'] < data['Low']
        if invalid_high_low.any():
            logger.warning(f"Found {invalid_high_low.sum()} rows where High < Low, fixing...")
            data.loc[invalid_high_low, 'High'] = data.loc[invalid_high_low, ['High', 'Low']].max(axis=1)
        
        # Fix High < Open: set High = max(High, Open)
        invalid_high_open = data['High'] < data['Open']
        if invalid_high_open.any():
            logger.warning(f"Found {invalid_high_open.sum()} rows where High < Open, fixing...")
            data.loc[invalid_high_open, 'High'] = data.loc[invalid_high_open, ['High', 'Open']].max(axis=1)
        
        # Fix High < Close: set High = max(High, Close)
        invalid_high_close = data['High'] < data['Close']
        if invalid_high_close.any():
            logger.warning(f"Found {invalid_high_close.sum()} rows where High < Close, fixing...")
            data.loc[invalid_high_close, 'High'] = data.loc[invalid_high_close, ['High', 'Close']].max(axis=1)
        
        # Fix Low > Open: set Low = min(Low, Open)
        invalid_low_open = data['Low'] > data['Open']
        if invalid_low_open.any():
            logger.warning(f"Found {invalid_low_open.sum()} rows where Low > Open, fixing...")
            data.loc[invalid_low_open, 'Low'] = data.loc[invalid_low_open, ['Low', 'Open']].min(axis=1)
        
        # Fix Low > Close: set Low = min(Low, Close)
        invalid_low_close = data['Low'] > data['Close']
        if invalid_low_close.any():
            logger.warning(f"Found {invalid_low_close.sum()} rows where Low > Close, fixing...")
            data.loc[invalid_low_close, 'Low'] = data.loc[invalid_low_close, ['Low', 'Close']].min(axis=1)
        
        # Fix negative Volume
        invalid_volume = data['Volume'] < 0
        if invalid_volume.any():
            logger.warning(f"Found {invalid_volume.sum()} rows with negative Volume, setting to 0...")
            data.loc[invalid_volume, 'Volume'] = 0
        
        return data
    
    def _validate_data_continuity(
        self,
        data: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> bool:
        """
        Validate that data is reasonably continuous (no large gaps).
        
        Args:
            data: DataFrame with OHLCV data
            start_date: Expected start date
            end_date: Expected end date
        
        Returns:
            True if data is continuous enough, False otherwise
        """
        if data.empty:
            return False
        
        # For small datasets (< 30 days), skip continuity checks
        if len(data) < 30:
            return True
        
        # Check if we have data close to start and end dates
        # Allow up to 7 days tolerance for weekends/holidays
        first_date = data.index.min()
        last_date = data.index.max()
        
        start_diff = abs((first_date - start_date).days)
        end_diff = abs((last_date - end_date).days)
        
        if start_diff > 7 or end_diff > 7:
            return False
        
        # Check for large gaps (> 10 days) in the data
        date_diffs = data.index.to_series().diff()
        max_gap = date_diffs.max()
        
        if pd.notna(max_gap) and max_gap.days > 10:
            return False
        
        return True
