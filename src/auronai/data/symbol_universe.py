"""
Symbol Universe Management for AuronAI.

This module defines the universe of tradeable symbols and provides
validation and management functionality.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from auronai.data.market_data_provider import MarketDataProvider
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


# ── Asset classification ───────────────────────────────────────────────


class AssetClass(str, Enum):
    """Asset class for symbol classification."""

    STOCK = "stock"
    ETF = "etf"
    LEVERAGED_ETF = "leveraged_etf"


@dataclass(frozen=True)
class SymbolInfo:
    """Enriched metadata for a tradeable symbol."""

    symbol: str
    asset_type: AssetClass
    sector: str
    beta_estimate: float
    min_volume: int
    is_pdt_safe: bool
    cfd_available: bool
    leverage_warning: str | None = None


# ── Symbol Universe Configuration ──────────────────────────────────────
# 53 symbols across 11 categories

SYMBOL_UNIVERSE: dict[str, list[str]] = {
    # US Equity Indices (3)
    "indices": ["SPY", "QQQ", "IWM"],
    # Sector ETFs (9)
    "sectors": [
        "XLK",  # Technology
        "XLF",  # Financials
        "XLE",  # Energy
        "XLV",  # Healthcare
        "XLI",  # Industrials
        "XLY",  # Consumer Discretionary
        "XLP",  # Consumer Staples
        "XLU",  # Utilities
        "XLB",  # Materials
    ],
    # Fixed Income (3)
    "bonds": [
        "TLT",  # 20+ Year Treasury
        "IEF",  # 7-10 Year Treasury
        "LQD",  # Investment Grade Corporate
    ],
    # Commodities (4)
    "commodities": [
        "GLD",  # Gold
        "SLV",  # Silver
        "DBC",  # Commodities Broad
        "USO",  # Oil
    ],
    # International (5)
    "international": [
        "EFA",  # Developed Markets
        "EEM",  # Emerging Markets
        "VGK",  # European Stocks
        "EWJ",  # Japan
        "FXI",  # China
    ],
    # Alternative (3)
    "alternatives": [
        "VNQ",  # Real Estate
        "HYG",  # High Yield Bonds
        "TIP",  # TIPS
    ],
    # ── New categories (Issue #19) ─────────────────────────────────────
    # Mega-cap stocks (8)
    "mega_caps": [
        "AAPL",  # Apple
        "MSFT",  # Microsoft
        "NVDA",  # NVIDIA
        "GOOGL",  # Alphabet
        "AMZN",  # Amazon
        "META",  # Meta Platforms
        "TSLA",  # Tesla
        "JPM",  # JPMorgan Chase
    ],
    # High-momentum / growth stocks (7)
    "momentum": [
        "AMD",  # Advanced Micro Devices
        "PLTR",  # Palantir
        "SOFI",  # SoFi Technologies
        "COIN",  # Coinbase
        "MARA",  # Marathon Digital
        "SQ",  # Block (Square)
        "SHOP",  # Shopify
    ],
    # Leveraged ETFs (4)
    "leveraged": [
        "TQQQ",  # 3x Bull Nasdaq-100
        "SQQQ",  # 3x Bear Nasdaq-100
        "UPRO",  # 3x Bull S&P 500
        "SPXU",  # 3x Bear S&P 500
    ],
    # Crypto ETFs (3)
    "crypto_etfs": [
        "BITO",  # ProShares Bitcoin Strategy
        "IBIT",  # iShares Bitcoin Trust
        "ETHA",  # iShares Ethereum Trust
    ],
    # Dividend / income (4)
    "dividend": [
        "SCHD",  # Schwab US Dividend Equity
        "VYM",  # Vanguard High Dividend Yield
        "JEPI",  # JPMorgan Equity Premium Income
        "O",  # Realty Income (monthly dividend REIT)
    ],
}


# ── Symbol Metadata ────────────────────────────────────────────────────


def _build_metadata() -> dict[str, SymbolInfo]:
    """Build the SYMBOL_METADATA dictionary."""
    m: dict[str, SymbolInfo] = {}

    # --- Indices (ETF) ---
    for sym, beta in [("SPY", 1.0), ("QQQ", 1.1), ("IWM", 1.2)]:
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.ETF,
            sector="broad_market",
            beta_estimate=beta,
            min_volume=5_000_000,
            is_pdt_safe=True,
            cfd_available=True,
        )

    # --- Sector ETFs ---
    sector_map = {
        "XLK": ("technology", 1.1),
        "XLF": ("financials", 1.1),
        "XLE": ("energy", 1.3),
        "XLV": ("healthcare", 0.8),
        "XLI": ("industrials", 1.0),
        "XLY": ("consumer_discretionary", 1.1),
        "XLP": ("consumer_staples", 0.6),
        "XLU": ("utilities", 0.5),
        "XLB": ("materials", 1.1),
    }
    for sym, (sector, beta) in sector_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.ETF,
            sector=sector,
            beta_estimate=beta,
            min_volume=2_000_000,
            is_pdt_safe=True,
            cfd_available=True,
        )

    # --- Bonds ---
    bond_map = {
        "TLT": ("treasury_long", -0.3),
        "IEF": ("treasury_mid", -0.1),
        "LQD": ("corporate_bonds", 0.1),
    }
    for sym, (sector, beta) in bond_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.ETF,
            sector=sector,
            beta_estimate=beta,
            min_volume=1_000_000,
            is_pdt_safe=True,
            cfd_available=True,
        )

    # --- Commodities ---
    commodity_map = {
        "GLD": ("gold", 0.0),
        "SLV": ("silver", 0.2),
        "DBC": ("commodities_broad", 0.3),
        "USO": ("oil", 0.5),
    }
    for sym, (sector, beta) in commodity_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.ETF,
            sector=sector,
            beta_estimate=beta,
            min_volume=1_000_000,
            is_pdt_safe=True,
            cfd_available=True,
        )

    # --- International ---
    intl_map = {
        "EFA": ("developed_intl", 0.9),
        "EEM": ("emerging_markets", 1.0),
        "VGK": ("europe", 0.9),
        "EWJ": ("japan", 0.7),
        "FXI": ("china", 1.1),
    }
    for sym, (sector, beta) in intl_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.ETF,
            sector=sector,
            beta_estimate=beta,
            min_volume=1_000_000,
            is_pdt_safe=True,
            cfd_available=True,
        )

    # --- Alternatives ---
    alt_map = {
        "VNQ": ("real_estate", 0.8),
        "HYG": ("high_yield", 0.4),
        "TIP": ("tips", 0.0),
    }
    for sym, (sector, beta) in alt_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.ETF,
            sector=sector,
            beta_estimate=beta,
            min_volume=1_000_000,
            is_pdt_safe=True,
            cfd_available=True,
        )

    # --- Mega-caps (STOCK) ---
    mega_map = {
        "AAPL": ("technology", 1.2),
        "MSFT": ("technology", 0.9),
        "NVDA": ("technology", 1.7),
        "GOOGL": ("technology", 1.1),
        "AMZN": ("consumer_discretionary", 1.2),
        "META": ("technology", 1.3),
        "TSLA": ("consumer_discretionary", 2.0),
        "JPM": ("financials", 1.1),
    }
    for sym, (sector, beta) in mega_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.STOCK,
            sector=sector,
            beta_estimate=beta,
            min_volume=5_000_000,
            is_pdt_safe=False,
            cfd_available=True,
        )

    # --- Momentum / Growth (STOCK) ---
    mom_map = {
        "AMD": ("technology", 1.8),
        "PLTR": ("technology", 1.9),
        "SOFI": ("financials", 1.8),
        "COIN": ("financials", 2.5),
        "MARA": ("crypto_mining", 3.5),
        "SQ": ("financials", 1.9),
        "SHOP": ("technology", 2.0),
    }
    for sym, (sector, beta) in mom_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.STOCK,
            sector=sector,
            beta_estimate=beta,
            min_volume=2_000_000,
            is_pdt_safe=False,
            cfd_available=True,
        )

    # --- Leveraged ETFs ---
    lev_map = {
        "TQQQ": (
            "leveraged_bull",
            3.0,
            "3x leveraged: daily rebalancing causes decay; not suitable for long-term holds",
        ),
        "SQQQ": (
            "leveraged_bear",
            -3.0,
            "3x inverse leveraged: daily rebalancing "
            "causes decay; not suitable for long-term holds",
        ),
        "UPRO": (
            "leveraged_bull",
            3.0,
            "3x leveraged: daily rebalancing causes decay; not suitable for long-term holds",
        ),
        "SPXU": (
            "leveraged_bear",
            -3.0,
            "3x inverse leveraged: daily rebalancing "
            "causes decay; not suitable for long-term holds",
        ),
    }
    for sym, (sector, beta, warning) in lev_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.LEVERAGED_ETF,
            sector=sector,
            beta_estimate=beta,
            min_volume=5_000_000,
            is_pdt_safe=True,
            cfd_available=True,
            leverage_warning=warning,
        )

    # --- Crypto ETFs ---
    crypto_map = {
        "BITO": ("crypto", 1.8),
        "IBIT": ("crypto", 1.8),
        "ETHA": ("crypto", 2.0),
    }
    for sym, (sector, beta) in crypto_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.ETF,
            sector=sector,
            beta_estimate=beta,
            min_volume=1_000_000,
            is_pdt_safe=True,
            cfd_available=True,
        )

    # --- Dividend / Income ---
    div_map = {
        "SCHD": ("dividend", 0.8),
        "VYM": ("dividend", 0.8),
        "JEPI": ("dividend", 0.6),
    }
    for sym, (sector, beta) in div_map.items():
        m[sym] = SymbolInfo(
            symbol=sym,
            asset_type=AssetClass.ETF,
            sector=sector,
            beta_estimate=beta,
            min_volume=1_000_000,
            is_pdt_safe=True,
            cfd_available=True,
        )
    # O is a REIT stock, not an ETF
    m["O"] = SymbolInfo(
        symbol="O",
        asset_type=AssetClass.STOCK,
        sector="real_estate",
        beta_estimate=0.7,
        min_volume=2_000_000,
        is_pdt_safe=False,
        cfd_available=True,
    )

    return m


SYMBOL_METADATA: dict[str, SymbolInfo] = _build_metadata()


# ── Validation ─────────────────────────────────────────────────────────


@dataclass
class ValidationResult:
    """Results from symbol universe validation."""

    valid: list[str]
    insufficient_data: list[str]
    missing: list[str]
    errors: list[str]

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


# ── Manager ────────────────────────────────────────────────────────────


class SymbolUniverseManager:
    """
    Manages the universe of tradeable symbols.

    Handles data validation, availability checks,
    and symbol categorization.
    """

    def __init__(self, market_data_provider: MarketDataProvider):
        self.provider = market_data_provider
        self.universe = self._load_universe()
        self.validated_symbols: list[str] = []

        logger.info(f"SymbolUniverseManager initialized with {len(self.get_all_symbols())} symbols")

    def _load_universe(self) -> dict[str, list[str]]:
        """Load symbol universe from configuration."""
        return SYMBOL_UNIVERSE

    def get_all_symbols(self) -> list[str]:
        """Get flat list of all symbols in the universe."""
        symbols = []
        for category in self.universe.values():
            symbols.extend(category)
        return symbols

    def get_symbols_by_category(self, category: str) -> list[str]:
        """Get symbols for a specific category."""
        if category not in self.universe:
            raise ValueError(
                f"Unknown category: {category}. Available: {list(self.universe.keys())}"
            )
        return self.universe[category]

    def get_validated_symbols(self) -> list[str]:
        """Get list of validated symbols ready for trading."""
        if not self.validated_symbols:
            raise ValueError("No validated symbols available. Call validate_universe() first.")
        return self.validated_symbols

    # ── Metadata queries ───────────────────────────────────────────

    def get_symbol_metadata(self, symbol: str) -> SymbolInfo | None:
        """Get metadata for a single symbol."""
        return SYMBOL_METADATA.get(symbol)

    def get_all_metadata(self) -> dict[str, SymbolInfo]:
        """Get full metadata dictionary."""
        return SYMBOL_METADATA

    def get_symbols_by_asset_type(self, asset_type: AssetClass) -> list[str]:
        """Get symbols filtered by asset type."""
        return [sym for sym, info in SYMBOL_METADATA.items() if info.asset_type == asset_type]

    def get_pdt_safe_symbols(self) -> list[str]:
        """Get symbols safe for PDT-restricted accounts."""
        return [sym for sym, info in SYMBOL_METADATA.items() if info.is_pdt_safe]

    def get_cfd_available_symbols(self) -> list[str]:
        """Get symbols available for CFD trading."""
        return [sym for sym, info in SYMBOL_METADATA.items() if info.cfd_available]

    def get_leveraged_warnings(self) -> dict[str, str]:
        """Get leverage warnings for symbols that have them."""
        return {
            sym: info.leverage_warning
            for sym, info in SYMBOL_METADATA.items()
            if info.leverage_warning is not None
        }

    # ── Validation ─────────────────────────────────────────────────

    def validate_universe(
        self,
        start_date: datetime,
        end_date: datetime,
        min_data_points: int = 756,  # 3 years of trading days
    ) -> ValidationResult:
        """Validate data availability for all symbols."""
        logger.info(f"Validating symbol universe from {start_date.date()} to {end_date.date()}")
        logger.info(f"Minimum data points required: {min_data_points}")

        result = ValidationResult(
            valid=[],
            insufficient_data=[],
            missing=[],
            errors=[],
        )

        all_symbols = self.get_all_symbols()

        for symbol in all_symbols:
            try:
                data = self.provider.get_historical_data_range(
                    symbol,
                    start_date,
                    end_date,
                )

                if data is None:
                    logger.warning(f"[MISS] {symbol}: No data available")
                    result.missing.append(symbol)
                elif len(data) < min_data_points:
                    logger.warning(
                        f"[INSUF] {symbol}: Insufficient data ({len(data)} < {min_data_points})"
                    )
                    result.insufficient_data.append(symbol)
                else:
                    logger.info(f"[OK] {symbol}: Valid ({len(data)} data points)")
                    result.valid.append(symbol)

            except Exception as e:
                logger.error(f"[ERR] {symbol}: Error during validation: {e}")
                result.errors.append(symbol)

        self.validated_symbols = result.valid

        logger.info("\n" + "=" * 80)
        logger.info("SYMBOL UNIVERSE VALIDATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total symbols checked: {result.total_symbols}")
        logger.info(f"Valid: {len(result.valid)}")
        logger.info(f"Insufficient data: {len(result.insufficient_data)}")
        logger.info(f"Missing: {len(result.missing)}")
        logger.info(f"Errors: {len(result.errors)}")
        logger.info(f"Success rate: {result.success_rate:.1%}")
        logger.info("=" * 80)

        if result.insufficient_data:
            logger.warning(f"Symbols with insufficient data: {result.insufficient_data}")
        if result.missing:
            logger.warning(f"Missing symbols: {result.missing}")
        if result.errors:
            logger.error(f"Symbols with errors: {result.errors}")

        return result
