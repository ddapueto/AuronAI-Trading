"""
Unit tests for Symbol Universe Manager.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import pandas as pd

from auronai.data.symbol_universe import (
    SymbolUniverseManager,
    ValidationResult,
    SYMBOL_UNIVERSE
)
from auronai.data.market_data_provider import MarketDataProvider


class TestSymbolUniverse:
    """Test suite for symbol universe configuration."""
    
    def test_symbol_universe_has_all_categories(self):
        """Test that SYMBOL_UNIVERSE has all required categories."""
        expected_categories = [
            'indices', 'sectors', 'bonds', 'commodities',
            'international', 'alternatives'
        ]
        
        for category in expected_categories:
            assert category in SYMBOL_UNIVERSE, f"Missing category: {category}"
    
    def test_symbol_universe_has_minimum_symbols(self):
        """Test that universe has at least 27 symbols."""
        total_symbols = sum(len(symbols) for symbols in SYMBOL_UNIVERSE.values())
        assert total_symbols >= 27, f"Expected >= 27 symbols, got {total_symbols}"
    
    def test_no_duplicate_symbols(self):
        """Test that there are no duplicate symbols across categories."""
        all_symbols = []
        for symbols in SYMBOL_UNIVERSE.values():
            all_symbols.extend(symbols)
        
        assert len(all_symbols) == len(set(all_symbols)), "Duplicate symbols found"


class TestSymbolUniverseManager:
    """Test suite for SymbolUniverseManager class."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock market data provider."""
        return Mock(spec=MarketDataProvider)
    
    @pytest.fixture
    def manager(self, mock_provider):
        """Create SymbolUniverseManager instance."""
        return SymbolUniverseManager(mock_provider)
    
    def test_init(self, manager, mock_provider):
        """Test initialization."""
        assert manager.provider == mock_provider
        assert manager.universe == SYMBOL_UNIVERSE
        assert manager.validated_symbols == []
    
    def test_get_all_symbols_returns_correct_count(self, manager):
        """Test get_all_symbols returns all symbols."""
        symbols = manager.get_all_symbols()
        
        expected_count = sum(len(s) for s in SYMBOL_UNIVERSE.values())
        assert len(symbols) == expected_count
    
    def test_get_all_symbols_returns_list(self, manager):
        """Test get_all_symbols returns a list."""
        symbols = manager.get_all_symbols()
        assert isinstance(symbols, list)
    
    def test_get_symbols_by_category(self, manager):
        """Test getting symbols by category."""
        indices = manager.get_symbols_by_category('indices')
        assert indices == SYMBOL_UNIVERSE['indices']
        
        sectors = manager.get_symbols_by_category('sectors')
        assert sectors == SYMBOL_UNIVERSE['sectors']
    
    def test_get_symbols_by_invalid_category_raises_error(self, manager):
        """Test that invalid category raises ValueError."""
        with pytest.raises(ValueError, match="Unknown category"):
            manager.get_symbols_by_category('invalid_category')
    
    def test_get_validated_symbols_before_validation_raises_error(self, manager):
        """Test that getting validated symbols before validation raises error."""
        with pytest.raises(ValueError, match="Call validate_universe"):
            manager.get_validated_symbols()
    
    def test_validate_universe_with_all_valid_symbols(self, manager, mock_provider):
        """Test validation when all symbols have sufficient data."""
        # Create mock data with enough rows
        mock_data = pd.DataFrame({
            'Open': [100.0] * 800,
            'High': [101.0] * 800,
            'Low': [99.0] * 800,
            'Close': [100.5] * 800,
            'Volume': [1000000] * 800
        }, index=pd.date_range('2020-01-01', periods=800))
        
        # Mock provider to return valid data for all symbols
        mock_provider.get_historical_data_range = Mock(return_value=mock_data)
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)
        
        result = manager.validate_universe(start_date, end_date, min_data_points=756)
        
        # All symbols should be valid
        assert len(result.valid) == len(manager.get_all_symbols())
        assert len(result.insufficient_data) == 0
        assert len(result.missing) == 0
        assert len(result.errors) == 0
        assert result.success_rate == 1.0
    
    def test_validate_universe_with_insufficient_data(self, manager, mock_provider):
        """Test validation when symbols have insufficient data."""
        # Create mock data with too few rows
        mock_data = pd.DataFrame({
            'Open': [100.0] * 500,
            'High': [101.0] * 500,
            'Low': [99.0] * 500,
            'Close': [100.5] * 500,
            'Volume': [1000000] * 500
        }, index=pd.date_range('2020-01-01', periods=500))
        
        mock_provider.get_historical_data_range = Mock(return_value=mock_data)
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)
        
        result = manager.validate_universe(start_date, end_date, min_data_points=756)
        
        # All symbols should have insufficient data
        assert len(result.valid) == 0
        assert len(result.insufficient_data) == len(manager.get_all_symbols())
        assert len(result.missing) == 0
        assert len(result.errors) == 0
    
    def test_validate_universe_with_missing_symbols(self, manager, mock_provider):
        """Test validation when symbols are missing."""
        # Mock provider to return None (missing data)
        mock_provider.get_historical_data_range = Mock(return_value=None)
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)
        
        result = manager.validate_universe(start_date, end_date)
        
        # All symbols should be missing
        assert len(result.valid) == 0
        assert len(result.insufficient_data) == 0
        assert len(result.missing) == len(manager.get_all_symbols())
        assert len(result.errors) == 0
    
    def test_validate_universe_with_errors(self, manager, mock_provider):
        """Test validation when errors occur."""
        # Mock provider to raise exception
        mock_provider.get_historical_data_range = Mock(
            side_effect=Exception("API error")
        )
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)
        
        result = manager.validate_universe(start_date, end_date)
        
        # All symbols should have errors
        assert len(result.valid) == 0
        assert len(result.insufficient_data) == 0
        assert len(result.missing) == 0
        assert len(result.errors) == len(manager.get_all_symbols())
    
    def test_validate_universe_mixed_results(self, manager, mock_provider):
        """Test validation with mixed results."""
        all_symbols = manager.get_all_symbols()
        
        def mock_get_data(symbol, start, end):
            """Mock function that returns different results per symbol."""
            if symbol in all_symbols[:5]:
                # First 5: valid data
                return pd.DataFrame({
                    'Open': [100.0] * 800,
                    'High': [101.0] * 800,
                    'Low': [99.0] * 800,
                    'Close': [100.5] * 800,
                    'Volume': [1000000] * 800
                }, index=pd.date_range('2020-01-01', periods=800))
            elif symbol in all_symbols[5:10]:
                # Next 5: insufficient data
                return pd.DataFrame({
                    'Open': [100.0] * 500,
                    'High': [101.0] * 500,
                    'Low': [99.0] * 500,
                    'Close': [100.5] * 500,
                    'Volume': [1000000] * 500
                }, index=pd.date_range('2020-01-01', periods=500))
            elif symbol in all_symbols[10:15]:
                # Next 5: missing
                return None
            else:
                # Rest: errors
                raise Exception("API error")
        
        mock_provider.get_historical_data_range = Mock(side_effect=mock_get_data)
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)
        
        result = manager.validate_universe(start_date, end_date, min_data_points=756)
        
        # Check that we have mixed results
        assert len(result.valid) == 5
        assert len(result.insufficient_data) == 5
        assert len(result.missing) == 5
        assert len(result.errors) > 0
        assert result.total_symbols == len(all_symbols)
    
    def test_validated_symbols_updated_after_validation(self, manager, mock_provider):
        """Test that validated_symbols is updated after validation."""
        # Create mock valid data
        mock_data = pd.DataFrame({
            'Open': [100.0] * 800,
            'High': [101.0] * 800,
            'Low': [99.0] * 800,
            'Close': [100.5] * 800,
            'Volume': [1000000] * 800
        }, index=pd.date_range('2020-01-01', periods=800))
        
        mock_provider.get_historical_data_range = Mock(return_value=mock_data)
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)
        
        result = manager.validate_universe(start_date, end_date)
        
        # validated_symbols should be updated
        assert manager.validated_symbols == result.valid
        assert len(manager.get_validated_symbols()) > 0


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""
    
    def test_total_symbols(self):
        """Test total_symbols property."""
        result = ValidationResult(
            valid=['AAPL', 'MSFT'],
            insufficient_data=['GOOGL'],
            missing=['TSLA'],
            errors=['AMZN']
        )
        
        assert result.total_symbols == 5
    
    def test_success_rate(self):
        """Test success_rate property."""
        result = ValidationResult(
            valid=['AAPL', 'MSFT', 'GOOGL'],
            insufficient_data=['TSLA'],
            missing=['AMZN'],
            errors=[]
        )
        
        assert result.success_rate == 0.6  # 3 valid out of 5 total
    
    def test_success_rate_with_no_symbols(self):
        """Test success_rate when no symbols."""
        result = ValidationResult(
            valid=[],
            insufficient_data=[],
            missing=[],
            errors=[]
        )
        
        assert result.success_rate == 0.0
