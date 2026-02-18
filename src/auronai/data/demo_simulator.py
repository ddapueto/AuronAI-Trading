"""Demo simulator for generating realistic market data without network calls.

This module provides offline market data generation using geometric Brownian motion
for testing and demonstration purposes.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


class DemoSimulator:
    """Generate realistic simulated market data for offline operation."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize demo simulator.
        
        Args:
            seed: Random seed for reproducible results
        """
        if seed is not None:
            np.random.seed(seed)
    
    def generate_price_data(
        self,
        symbol: str,
        days: int = 30,
        initial_price: float = 100.0,
        volatility: float = 0.02,
        drift: float = 0.0005,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """Generate simulated OHLCV data using geometric Brownian motion.
        
        Args:
            symbol: Stock symbol
            days: Number of days to generate
            initial_price: Starting price
            volatility: Daily volatility (standard deviation)
            drift: Daily drift (mean return)
            interval: Time interval ('1d' for daily, '1h' for hourly)
            
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
            
        **Validates: Requirements 6.1, 6.2**
        """
        # Calculate number of periods based on interval
        if interval == '1d':
            periods = days
        elif interval == '1h':
            periods = days * 24
        elif interval == '15m':
            periods = days * 24 * 4
        else:
            periods = days
        
        # Generate returns using geometric Brownian motion
        # dS/S = drift*dt + volatility*dW
        dt = 1.0  # time step
        returns = np.random.normal(drift * dt, volatility * np.sqrt(dt), periods)
        
        # Calculate prices from returns
        price_series = initial_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC data
        data = []
        for i, close_price in enumerate(price_series):
            # Generate intraday volatility for OHLC
            intraday_vol = volatility * 0.5  # Intraday is typically lower
            
            # Open is previous close (or initial price for first period)
            if i == 0:
                open_price = initial_price
            else:
                open_price = price_series[i - 1]
            
            # Generate high and low around the open-close range
            price_range = abs(close_price - open_price)
            high_extra = np.random.exponential(price_range * 0.5)
            low_extra = np.random.exponential(price_range * 0.5)
            
            high = max(open_price, close_price) + high_extra
            low = min(open_price, close_price) - low_extra
            
            # Ensure valid OHLC relationships
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Generate volume correlated with price movement
            price_change_pct = abs(close_price - open_price) / open_price
            base_volume = 1_000_000
            volume_multiplier = 1.0 + (price_change_pct * 10)  # More volume on big moves
            volume = int(base_volume * volume_multiplier * np.random.uniform(0.5, 1.5))
            
            data.append({
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': close_price,
                'Volume': volume
            })
        
        # Create DataFrame with datetime index
        df = pd.DataFrame(data)
        
        # Generate timestamps
        if interval == '1d':
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=days),
                periods=periods,
                freq='D'
            )
        elif interval == '1h':
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=days),
                periods=periods,
                freq='h'
            )
        elif interval == '15m':
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=days),
                periods=periods,
                freq='15min'
            )
        else:
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=days),
                periods=periods,
                freq='D'
            )
        
        df.index = dates
        return df
    
    def generate_trending_market(
        self,
        symbol: str,
        days: int = 30,
        initial_price: float = 100.0,
        direction: str = 'up',
        strength: float = 0.02,
        volatility: float = 0.015
    ) -> pd.DataFrame:
        """Generate data with a specific trend direction.
        
        Args:
            symbol: Stock symbol
            days: Number of days to generate
            initial_price: Starting price
            direction: 'up' for uptrend, 'down' for downtrend
            strength: Trend strength (daily drift)
            volatility: Daily volatility
            
        Returns:
            DataFrame with trending price data
            
        **Validates: Requirements 6.2**
        """
        # Set drift based on direction
        if direction == 'up':
            drift = abs(strength)
        elif direction == 'down':
            drift = -abs(strength)
        else:
            drift = 0.0
        
        return self.generate_price_data(
            symbol=symbol,
            days=days,
            initial_price=initial_price,
            volatility=volatility,
            drift=drift
        )
    
    def add_market_noise(
        self,
        data: pd.DataFrame,
        noise_level: float = 0.01
    ) -> pd.DataFrame:
        """Add realistic price fluctuations to existing data.
        
        Args:
            data: DataFrame with OHLCV data
            noise_level: Amount of noise to add (as fraction of price)
            
        Returns:
            DataFrame with added noise
            
        **Validates: Requirements 6.2**
        """
        df = data.copy()
        
        for i in range(len(df)):
            # Add noise to each price
            noise = np.random.normal(0, noise_level)
            
            # Apply noise while maintaining OHLC relationships
            close_noise = df.iloc[i]['Close'] * noise
            df.iloc[i, df.columns.get_loc('Close')] += close_noise
            
            # Adjust high and low to maintain validity
            if df.iloc[i]['Close'] > df.iloc[i]['High']:
                df.iloc[i, df.columns.get_loc('High')] = df.iloc[i]['Close']
            if df.iloc[i]['Close'] < df.iloc[i]['Low']:
                df.iloc[i, df.columns.get_loc('Low')] = df.iloc[i]['Close']
        
        return df
    
    def generate_multiple_symbols(
        self,
        symbols: list[str],
        days: int = 30,
        **kwargs
    ) -> dict[str, pd.DataFrame]:
        """Generate data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            days: Number of days to generate
            **kwargs: Additional arguments for generate_price_data
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        return {
            symbol: self.generate_price_data(symbol, days, **kwargs)
            for symbol in symbols
        }
