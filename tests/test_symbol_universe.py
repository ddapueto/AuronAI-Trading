"""
Unit tests for Symbol Universe Manager.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
import pandas as pd

from auronai.data.symbol_universe import (
    AssetClass,
    SymbolInfo,
    SymbolUniverseManager,
    ValidationResult,
    SYMBOL_METADATA,
    SYMBOL_UNIVERSE,
)
from auronai.data.market_data_provider import MarketDataProvider


class TestSymbolUniverse:
    """Test suite for symbol universe configuration."""

    def test_symbol_universe_has_all_categories(self):
        """Test that SYMBOL_UNIVERSE has all 11 required categories."""
        expected_categories = [
            'indices', 'sectors', 'bonds', 'commodities',
            'international', 'alternatives',
            'mega_caps', 'momentum', 'leveraged',
            'crypto_etfs', 'dividend',
        ]

        for category in expected_categories:
            assert category in SYMBOL_UNIVERSE, (
                f"Missing category: {category}"
            )
        assert len(SYMBOL_UNIVERSE) == 11

    def test_symbol_universe_has_minimum_symbols(self):
        """Test that universe has at least 50 symbols."""
        total_symbols = sum(
            len(symbols) for symbols in SYMBOL_UNIVERSE.values()
        )
        assert total_symbols >= 50, (
            f"Expected >= 50 symbols, got {total_symbols}"
        )

    def test_no_duplicate_symbols(self):
        """Test that there are no duplicate symbols across categories."""
        all_symbols = []
        for symbols in SYMBOL_UNIVERSE.values():
            all_symbols.extend(symbols)

        assert len(all_symbols) == len(set(all_symbols)), (
            "Duplicate symbols found"
        )


class TestSymbolMetadata:
    """Test suite for SYMBOL_METADATA consistency."""

    def test_every_symbol_has_metadata(self):
        """Every symbol in SYMBOL_UNIVERSE must have metadata."""
        all_symbols = []
        for symbols in SYMBOL_UNIVERSE.values():
            all_symbols.extend(symbols)

        for sym in all_symbols:
            assert sym in SYMBOL_METADATA, (
                f"Symbol {sym} missing from SYMBOL_METADATA"
            )

    def test_no_metadata_without_universe_entry(self):
        """Every symbol in SYMBOL_METADATA must exist in SYMBOL_UNIVERSE."""
        all_symbols = set()
        for symbols in SYMBOL_UNIVERSE.values():
            all_symbols.update(symbols)

        for sym in SYMBOL_METADATA:
            assert sym in all_symbols, (
                f"Metadata key {sym} not in SYMBOL_UNIVERSE"
            )

    def test_metadata_symbol_field_matches_key(self):
        """SymbolInfo.symbol must match its dict key."""
        for key, info in SYMBOL_METADATA.items():
            assert info.symbol == key, (
                f"Key {key} != info.symbol {info.symbol}"
            )

    def test_leveraged_etfs_have_warnings(self):
        """All LEVERAGED_ETF symbols must have a leverage_warning."""
        for sym, info in SYMBOL_METADATA.items():
            if info.asset_type == AssetClass.LEVERAGED_ETF:
                assert info.leverage_warning is not None, (
                    f"Leveraged ETF {sym} missing leverage_warning"
                )
                assert len(info.leverage_warning) > 0

    def test_beta_estimates_reasonable(self):
        """Beta estimates should be in range [-4, 5]."""
        for sym, info in SYMBOL_METADATA.items():
            assert -4.0 <= info.beta_estimate <= 5.0, (
                f"{sym} beta {info.beta_estimate} out of range"
            )


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

        expected_count = sum(
            len(s) for s in SYMBOL_UNIVERSE.values()
        )
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

    def test_get_symbols_by_invalid_category_raises_error(
        self, manager
    ):
        """Test that invalid category raises ValueError."""
        with pytest.raises(ValueError, match="Unknown category"):
            manager.get_symbols_by_category('invalid_category')

    def test_get_validated_symbols_before_validation_raises_error(
        self, manager
    ):
        """Test that getting validated symbols before validation raises error."""
        with pytest.raises(
            ValueError, match="Call validate_universe"
        ):
            manager.get_validated_symbols()

    def test_validate_universe_with_all_valid_symbols(
        self, manager, mock_provider
    ):
        """Test validation when all symbols have sufficient data."""
        mock_data = pd.DataFrame(
            {
                'Open': [100.0] * 800,
                'High': [101.0] * 800,
                'Low': [99.0] * 800,
                'Close': [100.5] * 800,
                'Volume': [1000000] * 800,
            },
            index=pd.date_range('2020-01-01', periods=800),
        )

        mock_provider.get_historical_data_range = Mock(
            return_value=mock_data
        )

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)

        result = manager.validate_universe(
            start_date, end_date, min_data_points=756
        )

        assert len(result.valid) == len(manager.get_all_symbols())
        assert len(result.insufficient_data) == 0
        assert len(result.missing) == 0
        assert len(result.errors) == 0
        assert result.success_rate == 1.0

    def test_validate_universe_with_insufficient_data(
        self, manager, mock_provider
    ):
        """Test validation when symbols have insufficient data."""
        mock_data = pd.DataFrame(
            {
                'Open': [100.0] * 500,
                'High': [101.0] * 500,
                'Low': [99.0] * 500,
                'Close': [100.5] * 500,
                'Volume': [1000000] * 500,
            },
            index=pd.date_range('2020-01-01', periods=500),
        )

        mock_provider.get_historical_data_range = Mock(
            return_value=mock_data
        )

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)

        result = manager.validate_universe(
            start_date, end_date, min_data_points=756
        )

        assert len(result.valid) == 0
        assert len(result.insufficient_data) == len(
            manager.get_all_symbols()
        )
        assert len(result.missing) == 0
        assert len(result.errors) == 0

    def test_validate_universe_with_missing_symbols(
        self, manager, mock_provider
    ):
        """Test validation when symbols are missing."""
        mock_provider.get_historical_data_range = Mock(
            return_value=None
        )

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)

        result = manager.validate_universe(start_date, end_date)

        assert len(result.valid) == 0
        assert len(result.insufficient_data) == 0
        assert len(result.missing) == len(
            manager.get_all_symbols()
        )
        assert len(result.errors) == 0

    def test_validate_universe_with_errors(
        self, manager, mock_provider
    ):
        """Test validation when errors occur."""
        mock_provider.get_historical_data_range = Mock(
            side_effect=Exception("API error")
        )

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)

        result = manager.validate_universe(start_date, end_date)

        assert len(result.valid) == 0
        assert len(result.insufficient_data) == 0
        assert len(result.missing) == 0
        assert len(result.errors) == len(
            manager.get_all_symbols()
        )

    def test_validate_universe_mixed_results(
        self, manager, mock_provider
    ):
        """Test validation with mixed results."""
        all_symbols = manager.get_all_symbols()

        def mock_get_data(symbol, start, end):
            if symbol in all_symbols[:5]:
                return pd.DataFrame(
                    {
                        'Open': [100.0] * 800,
                        'High': [101.0] * 800,
                        'Low': [99.0] * 800,
                        'Close': [100.5] * 800,
                        'Volume': [1000000] * 800,
                    },
                    index=pd.date_range(
                        '2020-01-01', periods=800
                    ),
                )
            elif symbol in all_symbols[5:10]:
                return pd.DataFrame(
                    {
                        'Open': [100.0] * 500,
                        'High': [101.0] * 500,
                        'Low': [99.0] * 500,
                        'Close': [100.5] * 500,
                        'Volume': [1000000] * 500,
                    },
                    index=pd.date_range(
                        '2020-01-01', periods=500
                    ),
                )
            elif symbol in all_symbols[10:15]:
                return None
            else:
                raise Exception("API error")

        mock_provider.get_historical_data_range = Mock(
            side_effect=mock_get_data
        )

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)

        result = manager.validate_universe(
            start_date, end_date, min_data_points=756
        )

        assert len(result.valid) == 5
        assert len(result.insufficient_data) == 5
        assert len(result.missing) == 5
        assert len(result.errors) > 0
        assert result.total_symbols == len(all_symbols)

    def test_validated_symbols_updated_after_validation(
        self, manager, mock_provider
    ):
        """Test that validated_symbols is updated after validation."""
        mock_data = pd.DataFrame(
            {
                'Open': [100.0] * 800,
                'High': [101.0] * 800,
                'Low': [99.0] * 800,
                'Close': [100.5] * 800,
                'Volume': [1000000] * 800,
            },
            index=pd.date_range('2020-01-01', periods=800),
        )

        mock_provider.get_historical_data_range = Mock(
            return_value=mock_data
        )

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2023, 1, 1)

        result = manager.validate_universe(start_date, end_date)

        assert manager.validated_symbols == result.valid
        assert len(manager.get_validated_symbols()) > 0


class TestSymbolUniverseManagerMetadata:
    """Test suite for metadata query methods."""

    @pytest.fixture
    def manager(self):
        mock_provider = Mock(spec=MarketDataProvider)
        return SymbolUniverseManager(mock_provider)

    def test_get_symbol_metadata(self, manager):
        """Known symbol returns SymbolInfo."""
        info = manager.get_symbol_metadata('AAPL')
        assert info is not None
        assert info.symbol == 'AAPL'
        assert info.asset_type == AssetClass.STOCK

    def test_get_symbol_metadata_unknown(self, manager):
        """Unknown symbol returns None."""
        assert manager.get_symbol_metadata('ZZZZZ') is None

    def test_get_pdt_safe_symbols(self, manager):
        """PDT-safe list should contain only ETFs."""
        pdt_safe = manager.get_pdt_safe_symbols()
        assert len(pdt_safe) > 0
        for sym in pdt_safe:
            info = SYMBOL_METADATA[sym]
            assert info.is_pdt_safe is True

    def test_get_cfd_available_symbols(self, manager):
        """CFD available list is non-empty and consistent."""
        cfd = manager.get_cfd_available_symbols()
        assert len(cfd) > 0
        for sym in cfd:
            info = SYMBOL_METADATA[sym]
            assert info.cfd_available is True

    def test_get_leveraged_warnings(self, manager):
        """Leveraged warnings returns only symbols with warnings."""
        warnings = manager.get_leveraged_warnings()
        assert len(warnings) >= 4  # TQQQ, SQQQ, UPRO, SPXU
        for sym, warning in warnings.items():
            assert isinstance(warning, str)
            assert len(warning) > 0

    def test_get_symbols_by_asset_type(self, manager):
        """Filter by asset type returns correct symbols."""
        stocks = manager.get_symbols_by_asset_type(AssetClass.STOCK)
        assert 'AAPL' in stocks
        assert 'SPY' not in stocks

        etfs = manager.get_symbols_by_asset_type(AssetClass.ETF)
        assert 'SPY' in etfs
        assert 'AAPL' not in etfs

        lev = manager.get_symbols_by_asset_type(
            AssetClass.LEVERAGED_ETF
        )
        assert 'TQQQ' in lev
        assert len(lev) == 4

    def test_get_all_metadata(self, manager):
        """get_all_metadata returns complete dict."""
        meta = manager.get_all_metadata()
        assert len(meta) == len(SYMBOL_METADATA)


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""

    def test_total_symbols(self):
        """Test total_symbols property."""
        result = ValidationResult(
            valid=['AAPL', 'MSFT'],
            insufficient_data=['GOOGL'],
            missing=['TSLA'],
            errors=['AMZN'],
        )

        assert result.total_symbols == 5

    def test_success_rate(self):
        """Test success_rate property."""
        result = ValidationResult(
            valid=['AAPL', 'MSFT', 'GOOGL'],
            insufficient_data=['TSLA'],
            missing=['AMZN'],
            errors=[],
        )

        assert result.success_rate == 0.6

    def test_success_rate_with_no_symbols(self):
        """Test success_rate when no symbols."""
        result = ValidationResult(
            valid=[],
            insufficient_data=[],
            missing=[],
            errors=[],
        )

        assert result.success_rate == 0.0
