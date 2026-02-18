"""
DuckDB query engine for fast SQL queries over Parquet files.

This module provides a SQL interface to cached market data using DuckDB,
enabling fast analytical queries without loading full datasets into memory.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import duckdb
import pandas as pd


class DuckDBQueryEngine:
    """
    SQL query engine over Parquet files using DuckDB.
    
    Enables fast analytical queries without loading full datasets.
    DuckDB can query Parquet files directly without loading them into memory.
    
    Features:
    - Direct Parquet file queries
    - SQL interface for complex filtering
    - Aggregation and window functions
    - Connection pooling
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize DuckDBQueryEngine.
        
        Args:
            cache_dir: Root directory for cache storage (where Parquet files are)
        """
        self.cache_dir = Path(cache_dir)
        self.ohlcv_dir = self.cache_dir / "ohlcv"
        
        # Create in-memory DuckDB connection
        # In-memory is fast and suitable for read-only queries
        self.conn = duckdb.connect(":memory:")
        
        # Enable parallel query execution
        self.conn.execute("SET threads TO 4")
    
    def query_ohlcv(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Query OHLCV data using SQL.
        
        Args:
            symbols: List of stock symbols to query
            start_date: Start date for data range
            end_date: End date for data range
            columns: Optional list of columns to select (default: all)
        
        Returns:
            DataFrame with queried data, empty if no data found
        
        Example:
            >>> engine = DuckDBQueryEngine()
            >>> df = engine.query_ohlcv(
            ...     symbols=['AAPL', 'MSFT'],
            ...     start_date=datetime(2023, 1, 1),
            ...     end_date=datetime(2023, 12, 31),
            ...     columns=['Close', 'Volume']
            ... )
        """
        if not symbols:
            return pd.DataFrame()
        
        # Build list of Parquet files to query
        parquet_files = self._get_parquet_files(symbols, start_date, end_date)
        
        if not parquet_files:
            return pd.DataFrame()
        
        # Build column selection
        if columns:
            # Add 'index' (date) to columns if not present
            if 'index' not in columns:
                columns = ['index'] + columns
            col_select = ', '.join(columns)
        else:
            col_select = '*'
        
        # Build SQL query
        # DuckDB can read multiple Parquet files with glob patterns
        files_pattern = ', '.join(f"'{f}'" for f in parquet_files)
        
        # Note: Parquet saves DataFrame index as __index_level_0__
        query = f"""
            SELECT {col_select}
            FROM read_parquet([{files_pattern}])
            WHERE __index_level_0__ >= ? AND __index_level_0__ <= ?
            ORDER BY __index_level_0__
        """
        
        try:
            # Execute query with parameters
            result = self.conn.execute(
                query,
                [start_date, end_date]
            ).fetchdf()
            
            # Set index to date column if present
            if '__index_level_0__' in result.columns:
                result = result.set_index('__index_level_0__')
                result.index.name = None
            elif 'index' in result.columns:
                result = result.set_index('index')
                result.index.name = None
            
            return result
        
        except Exception as e:
            # Log error and return empty DataFrame
            print(f"DuckDB query error: {e}")
            return pd.DataFrame()
    
    def aggregate_metrics(
        self,
        symbol: str,
        metric: str,
        window: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Calculate rolling aggregates using SQL.
        
        Args:
            symbol: Stock symbol
            metric: Column name to aggregate (e.g., 'Volume', 'Close')
            window: Rolling window size in days
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            DataFrame with date, original metric, and rolling average
        
        Example:
            >>> engine = DuckDBQueryEngine()
            >>> df = engine.aggregate_metrics(
            ...     symbol='AAPL',
            ...     metric='Volume',
            ...     window=20
            ... )
            # Returns: date, Volume, Volume_MA20
        """
        # Get Parquet files for symbol
        symbol_dir = self.ohlcv_dir / symbol
        
        if not symbol_dir.exists():
            return pd.DataFrame()
        
        # Get all year files for symbol
        parquet_files = list(symbol_dir.glob("*.parquet"))
        
        if not parquet_files:
            return pd.DataFrame()
        
        # Build file pattern
        files_pattern = ', '.join(f"'{f}'" for f in parquet_files)
        
        # Build WHERE clause for date filtering
        where_clause = ""
        params = []
        
        if start_date and end_date:
            where_clause = "WHERE __index_level_0__ >= ? AND __index_level_0__ <= ?"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE __index_level_0__ >= ?"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE __index_level_0__ <= ?"
            params = [end_date]
        
        # Build SQL query with window function
        query = f"""
            SELECT
                __index_level_0__ as date,
                "{metric}",
                AVG("{metric}") OVER (
                    ORDER BY __index_level_0__
                    ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW
                ) as "{metric}_MA{window}"
            FROM read_parquet([{files_pattern}])
            {where_clause}
            ORDER BY __index_level_0__
        """
        
        try:
            if params:
                result = self.conn.execute(query, params).fetchdf()
            else:
                result = self.conn.execute(query).fetchdf()
            
            return result
        
        except Exception as e:
            print(f"DuckDB aggregation error: {e}")
            return pd.DataFrame()
    
    def get_symbol_stats(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[dict]:
        """
        Get summary statistics for a symbol.
        
        Args:
            symbol: Stock symbol
            start_date: Start date for analysis
            end_date: End date for analysis
        
        Returns:
            Dictionary with stats (min, max, avg, etc.) or None if no data
        
        Example:
            >>> engine = DuckDBQueryEngine()
            >>> stats = engine.get_symbol_stats(
            ...     symbol='AAPL',
            ...     start_date=datetime(2023, 1, 1),
            ...     end_date=datetime(2023, 12, 31)
            ... )
            # Returns: {'min_close': 150.0, 'max_close': 200.0, ...}
        """
        symbol_dir = self.ohlcv_dir / symbol
        
        if not symbol_dir.exists():
            return None
        
        # Get all year files
        parquet_files = list(symbol_dir.glob("*.parquet"))
        
        if not parquet_files:
            return None
        
        files_pattern = ', '.join(f"'{f}'" for f in parquet_files)
        
        query = f"""
            SELECT
                COUNT(*) as num_records,
                MIN("Close") as min_close,
                MAX("Close") as max_close,
                AVG("Close") as avg_close,
                MIN("Volume") as min_volume,
                MAX("Volume") as max_volume,
                AVG("Volume") as avg_volume
            FROM read_parquet([{files_pattern}])
            WHERE __index_level_0__ >= ? AND __index_level_0__ <= ?
        """
        
        try:
            result = self.conn.execute(query, [start_date, end_date]).fetchone()
            
            if result and result[0] > 0:
                return {
                    'num_records': result[0],
                    'min_close': result[1],
                    'max_close': result[2],
                    'avg_close': result[3],
                    'min_volume': result[4],
                    'max_volume': result[5],
                    'avg_volume': result[6]
                }
            
            return None
        
        except Exception as e:
            print(f"DuckDB stats error: {e}")
            return None
    
    def close(self) -> None:
        """Close DuckDB connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # Private methods
    
    def _get_parquet_files(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[Path]:
        """
        Get list of Parquet files to query based on symbols and date range.
        
        Args:
            symbols: List of symbols
            start_date: Start date
            end_date: End date
        
        Returns:
            List of Path objects for Parquet files
        """
        files = []
        
        start_year = start_date.year
        end_year = end_date.year
        
        for symbol in symbols:
            symbol_dir = self.ohlcv_dir / symbol
            
            if not symbol_dir.exists():
                continue
            
            # Get files for relevant years
            for year in range(start_year, end_year + 1):
                year_file = symbol_dir / f"{year}.parquet"
                
                if year_file.exists():
                    files.append(year_file)
        
        return files
