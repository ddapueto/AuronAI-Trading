"""
Symbol Universe Management for AuronAI.

This module defines the universe of tradeable symbols and provides
validation and management functionality.
"""

from typing import Dict, List
from datetime import datetime
from dataclasses import dataclass

from auronai.data.market_data_provider import MarketDataProvider
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


# Symbol Universe Configuration
# Based on Phase 1 requirements: minimum 27 symbols across categories
SYMBOL_UNIVERSE = {
    # US Equity Indices (3)
    'indices': ['SPY', 'QQQ', 'IWM'],
    
    # Sector ETFs (9)
    'sectors': [
        'XLK',  # Technology
        'XLF',  # Financials
        'XLE',  # Energy
        'XLV',  # Healthcare
        'XLI',  # Industrials
        'XLY',  # Consumer Discretionary
        'XLP',  # Consumer Staples
        'XLU',  # Utilities
        'XLB',  # Materials
    ],
    
    # Fixed Income (3)
    'bonds': [
        'TLT',  # 20+ Year Treasury
        'IEF',  # 7-10 Year Treasury
        'LQD',  # Investment Grade Corporate
    ],
    
    # Commodities (4)
    'commodities': [
        'GLD',  # Gold
        'SLV',  # Silver
        'DBC',  # Commodities Broad
        'USO',  # Oil
    ],
    
    # International (5)
    'international': [
        'EFA',  # Developed Markets
        'EEM',  # Emerging Markets
        'VGK',  # European Stocks
        'EWJ',  # Japan
        'FXI',  # China
    ],
    
    # Alternative (3)
    'alternatives': [
        'VNQ',  # Real Estate
        'HYG',  # High Yield Bonds
        'TIP',  # TIPS
    ],
}


@dataclass
class ValidationResult:
    """Results from symbol universe validation."""
    valid: List[str]
    insufficient_data: List[str]
    missing: List[str]
    errors: List[str]
    
    @property
    def total_symbols(self) -> int:
        """Total number of symbols checked."""
        return len(self.valid) + len(self.insufficient_data) + len(self.missing) + len(self.errors)
    
    @property
    def success_rate(self) -> float:
        """Percentage of symbols that passed validation."""
        if self.total_symbols == 0:
            return 0.0
        return len(self.valid) / self.total_symbols


class SymbolUniverseManager:
    """
    Manages the universe of tradeable symbols.
    
    Handles data validation, availability checks,
    and symbol categorization.
    """
    
    def __init__(self, market_data_provider: MarketDataProvider):
        """
        Initialize symbol universe manager.
        
        Args:
            market_data_provider: Provider for market data
        """
        self.provider = market_data_provider
        self.universe = self._load_universe()
        self.validated_symbols: List[str] = []
        
        logger.info(
            f"SymbolUniverseManager initialized with {len(self.get_all_symbols())} symbols"
        )
    
    def _load_universe(self) -> Dict[str, List[str]]:
        """
        Load symbol universe from configuration.
        
        Returns:
            Dictionary mapping category -> list of symbols
        """
        return SYMBOL_UNIVERSE
    
    def get_all_symbols(self) -> List[str]:
        """
        Get flat list of all symbols in the universe.
        
        Returns:
            List of all symbols across all categories
        """
        symbols = []
        for category in self.universe.values():
            symbols.extend(category)
        return symbols
    
    def get_symbols_by_category(self, category: str) -> List[str]:
        """
        Get symbols for a specific category.
        
        Args:
            category: Category name (e.g., 'indices', 'sectors')
        
        Returns:
            List of symbols in that category
        
        Raises:
            ValueError: If category doesn't exist
        """
        if category not in self.universe:
            raise ValueError(
                f"Unknown category: {category}. "
                f"Available: {list(self.universe.keys())}"
            )
        return self.universe[category]
    
    def get_validated_symbols(self) -> List[str]:
        """
        Get list of validated symbols ready for trading.
        
        Returns:
            List of symbols that passed validation
        
        Raises:
            ValueError: If validate_universe() hasn't been called yet
        """
        if not self.validated_symbols:
            raise ValueError(
                "No validated symbols available. "
                "Call validate_universe() first."
            )
        return self.validated_symbols
    
    def validate_universe(
        self,
        start_date: datetime,
        end_date: datetime,
        min_data_points: int = 756  # 3 years of trading days
    ) -> ValidationResult:
        """
        Validate data availability for all symbols.
        
        Checks each symbol for:
        - Data availability
        - Sufficient history (min_data_points)
        - Data quality
        
        Args:
            start_date: Start date for validation
            end_date: End date for validation
            min_data_points: Minimum number of data points required (default: 756 = 3 years)
        
        Returns:
            ValidationResult with categorized symbols
        """
        logger.info(
            f"Validating symbol universe from {start_date.date()} to {end_date.date()}"
        )
        logger.info(f"Minimum data points required: {min_data_points}")
        
        result = ValidationResult(
            valid=[],
            insufficient_data=[],
            missing=[],
            errors=[]
        )
        
        all_symbols = self.get_all_symbols()
        
        for symbol in all_symbols:
            try:
                # Attempt to fetch data
                data = self.provider.get_historical_data_range(
                    symbol,
                    start_date,
                    end_date
                )
                
                if data is None:
                    logger.warning(f"❌ {symbol}: No data available")
                    result.missing.append(symbol)
                elif len(data) < min_data_points:
                    logger.warning(
                        f"⚠️ {symbol}: Insufficient data ({len(data)} < {min_data_points})"
                    )
                    result.insufficient_data.append(symbol)
                else:
                    logger.info(f"✅ {symbol}: Valid ({len(data)} data points)")
                    result.valid.append(symbol)
                    
            except Exception as e:
                logger.error(f"❌ {symbol}: Error during validation: {e}")
                result.errors.append(symbol)
        
        # Update validated symbols list
        self.validated_symbols = result.valid
        
        # Log summary
        logger.info("\n" + "=" * 80)
        logger.info("SYMBOL UNIVERSE VALIDATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total symbols checked: {result.total_symbols}")
        logger.info(f"✅ Valid: {len(result.valid)}")
        logger.info(f"⚠️ Insufficient data: {len(result.insufficient_data)}")
        logger.info(f"❌ Missing: {len(result.missing)}")
        logger.info(f"❌ Errors: {len(result.errors)}")
        logger.info(f"Success rate: {result.success_rate:.1%}")
        logger.info("=" * 80)
        
        if result.insufficient_data:
            logger.warning(f"Symbols with insufficient data: {result.insufficient_data}")
        if result.missing:
            logger.warning(f"Missing symbols: {result.missing}")
        if result.errors:
            logger.error(f"Symbols with errors: {result.errors}")
        
        return result
