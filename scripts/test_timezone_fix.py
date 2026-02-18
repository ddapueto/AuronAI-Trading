#!/usr/bin/env python3
"""
Test script to verify timezone handling fix.

This script tests that data from different sources (with different timezones)
can be properly aligned without causing timezone comparison errors.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime, timedelta
import pandas as pd

from auronai.data.market_data_provider import MarketDataProvider
from auronai.data.feature_store import FeatureStore
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def test_timezone_normalization():
    """Test that timezone normalization works correctly."""
    print("=" * 80)
    print("Testing Timezone Normalization")
    print("=" * 80)
    
    # Initialize providers
    market_data = MarketDataProvider()
    
    # Test 1: Fetch data for different symbols (may have different timezones)
    print("\n1. Fetching data for AAPL and QQQ...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    aapl_data = market_data.get_historical_data_range('AAPL', start_date, end_date)
    qqq_data = market_data.get_historical_data_range('QQQ', start_date, end_date)
    
    if aapl_data is None or qqq_data is None:
        print("❌ Failed to fetch data")
        return False
    
    print(f"✅ AAPL: {len(aapl_data)} rows")
    print(f"✅ QQQ: {len(qqq_data)} rows")
    
    # Check timezone status
    print("\n2. Checking timezone status...")
    
    aapl_tz = aapl_data.index.tz if hasattr(aapl_data.index, 'tz') else None
    qqq_tz = qqq_data.index.tz if hasattr(qqq_data.index, 'tz') else None
    
    print(f"AAPL timezone: {aapl_tz}")
    print(f"QQQ timezone: {qqq_tz}")
    
    if aapl_tz is not None or qqq_tz is not None:
        print("❌ Data still has timezone information (should be None)")
        return False
    
    print("✅ Both datasets are timezone-naive")
    
    # Test 2: Try to create DataFrame with both (this was failing before)
    print("\n3. Testing DataFrame creation with both indices...")
    
    try:
        aapl_returns = aapl_data['Close'].pct_change(20)
        qqq_returns = qqq_data['Close'].pct_change(20)
        
        # This should not raise timezone comparison error
        aligned = pd.DataFrame({
            'aapl': aapl_returns,
            'qqq': qqq_returns
        })
        
        print(f"✅ Successfully created aligned DataFrame: {len(aligned)} rows")
        
    except TypeError as e:
        if "tz-naive and tz-aware" in str(e):
            print(f"❌ Timezone comparison error still occurs: {e}")
            return False
        raise
    
    # Test 3: Test FeatureStore relative strength calculation
    print("\n4. Testing FeatureStore relative strength calculation...")
    
    try:
        feature_store = FeatureStore()
        
        # This was the failing operation
        relative_strength = feature_store._calculate_relative_strength(
            aapl_data,
            qqq_data
        )
        
        print(f"✅ Relative strength calculated: {len(relative_strength)} values")
        print(f"   Non-null values: {relative_strength.notna().sum()}")
        
    except TypeError as e:
        if "tz-naive and tz-aware" in str(e):
            print(f"❌ Timezone error in relative strength: {e}")
            return False
        raise
    
    print("\n" + "=" * 80)
    print("✅ All timezone tests passed!")
    print("=" * 80)
    
    return True


def test_different_benchmarks():
    """Test with different benchmark symbols."""
    print("\n" + "=" * 80)
    print("Testing Different Benchmarks")
    print("=" * 80)
    
    market_data = MarketDataProvider()
    feature_store = FeatureStore()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    # Test with different benchmarks
    benchmarks = ['QQQ', 'SPY', 'DIA', 'IWM']
    symbol = 'AAPL'
    
    print(f"\nTesting {symbol} against different benchmarks...")
    
    symbol_data = market_data.get_historical_data_range(symbol, start_date, end_date)
    
    if symbol_data is None:
        print(f"❌ Failed to fetch {symbol} data")
        return False
    
    for benchmark in benchmarks:
        print(f"\n  Testing with {benchmark}...")
        
        try:
            benchmark_data = market_data.get_historical_data_range(
                benchmark, start_date, end_date
            )
            
            if benchmark_data is None:
                print(f"    ⚠️  Could not fetch {benchmark} data")
                continue
            
            # Calculate relative strength
            rs = feature_store._calculate_relative_strength(
                symbol_data,
                benchmark_data
            )
            
            print(f"    ✅ {benchmark}: {rs.notna().sum()} valid RS values")
            
        except TypeError as e:
            if "tz-naive and tz-aware" in str(e):
                print(f"    ❌ Timezone error with {benchmark}: {e}")
                return False
            raise
        except Exception as e:
            print(f"    ⚠️  Error with {benchmark}: {e}")
    
    print("\n✅ All benchmark tests passed!")
    return True


def main():
    """Run all tests."""
    print("\n🔬 Timezone Fix Verification\n")
    
    try:
        # Test 1: Basic timezone normalization
        if not test_timezone_normalization():
            print("\n❌ Basic timezone test failed")
            return 1
        
        # Test 2: Different benchmarks
        if not test_different_benchmarks():
            print("\n❌ Benchmark test failed")
            return 1
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe timezone fix is working correctly.")
        print("You can now use different benchmarks without timezone errors.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n❌ Test failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
