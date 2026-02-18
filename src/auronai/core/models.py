"""Core data models for AuronAI trading system."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv


@dataclass
class MarketData:
    """Market data for a single symbol at a point in time."""
    
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    def validate(self) -> bool:
        """Ensure OHLC relationships are valid.
        
        Returns:
            True if data is valid, False otherwise
        """
        return (
            self.high >= max(self.open, self.close) and
            self.low <= min(self.open, self.close) and
            self.volume >= 0 and
            all(v > 0 for v in [self.open, self.high, self.low, self.close])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        """Create from dictionary."""
        return cls(
            symbol=data['symbol'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data['volume']
        )


@dataclass
class TechnicalIndicators:
    """Technical indicators for a symbol."""
    
    symbol: str
    timestamp: datetime
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None
    atr: Optional[float] = None
    obv: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TechnicalIndicators':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class TradingSignal:
    """Trading signal with confidence and supporting factors."""
    
    symbol: str
    timestamp: datetime
    action: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0-10
    strategy: str
    bullish_signals: List[str] = field(default_factory=list)
    bearish_signals: List[str] = field(default_factory=list)
    
    def is_actionable(self, min_confidence: float = 7.0) -> bool:
        """Check if signal meets confidence threshold.
        
        Args:
            min_confidence: Minimum confidence score required
            
        Returns:
            True if signal is actionable
        """
        return self.confidence >= min_confidence and self.action in ["BUY", "SELL"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'confidence': self.confidence,
            'strategy': self.strategy,
            'bullish_signals': self.bullish_signals,
            'bearish_signals': self.bearish_signals
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingSignal':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class TradePlan:
    """Complete trade plan with entry, exit, and risk parameters."""
    
    symbol: str
    action: str  # "BUY" or "SELL"
    position_size: int  # number of shares
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float  # dollar amount at risk
    reward_amount: float  # potential profit
    rr_ratio: float  # risk-reward ratio
    
    def validate(self) -> Tuple[bool, str]:
        """Validate trade plan parameters.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.position_size <= 0:
            return False, "Position size must be positive"
        
        if self.action == "BUY":
            if self.stop_loss >= self.entry_price:
                return False, "Stop loss must be below entry for long positions"
            if self.take_profit <= self.entry_price:
                return False, "Take profit must be above entry for long positions"
        elif self.action == "SELL":
            if self.stop_loss <= self.entry_price:
                return False, "Stop loss must be above entry for short positions"
            if self.take_profit >= self.entry_price:
                return False, "Take profit must be below entry for short positions"
        else:
            return False, f"Invalid action: {self.action}"
        
        if self.rr_ratio < 1.5:
            return False, "Risk-reward ratio must be at least 1.5:1"
        
        return True, "Valid"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradePlan':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    
    strategy: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    trades: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['start_date'] = self.start_date.isoformat()
        result['end_date'] = self.end_date.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestResult':
        """Create from dictionary."""
        data = data.copy()
        data['start_date'] = datetime.fromisoformat(data['start_date'])
        data['end_date'] = datetime.fromisoformat(data['end_date'])
        return cls(**data)


@dataclass
class TradingConfig:
    """Configuration for trading system."""
    
    mode: str = "analysis"  # "analysis", "paper", "live"
    portfolio_value: float = 10000.0
    max_risk_per_trade: float = 0.02
    max_position_size: float = 0.20
    max_portfolio_exposure: float = 0.80
    strategy: str = "swing_weekly"
    symbols: List[str] = field(default_factory=lambda: ["AAPL", "MSFT", "NVDA"])
    use_claude: bool = True
    anthropic_api_key: Optional[str] = None
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'TradingConfig':
        """Load configuration from environment variables.
        
        Returns:
            TradingConfig instance with values from .env file
        """
        load_dotenv()
        
        return cls(
            mode=os.getenv('TRADING_MODE', 'analysis'),
            portfolio_value=float(os.getenv('PORTFOLIO_VALUE', '10000.0')),
            max_risk_per_trade=float(os.getenv('MAX_RISK_PER_TRADE', '0.02')),
            max_position_size=float(os.getenv('MAX_POSITION_SIZE', '0.20')),
            max_portfolio_exposure=float(os.getenv('MAX_PORTFOLIO_EXPOSURE', '0.80')),
            strategy=os.getenv('STRATEGY', 'swing_weekly'),
            symbols=os.getenv('SYMBOLS', 'AAPL,MSFT,NVDA').split(','),
            use_claude=os.getenv('USE_CLAUDE', 'true').lower() == 'true',
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            alpaca_api_key=os.getenv('ALPACA_API_KEY'),
            alpaca_secret_key=os.getenv('ALPACA_SECRET_KEY')
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration parameters.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate mode
        if self.mode not in ['analysis', 'paper', 'live']:
            errors.append(f"Invalid mode: {self.mode}. Must be 'analysis', 'paper', or 'live'")
        
        # Validate risk parameters
        if not 0 < self.max_risk_per_trade <= 0.05:
            errors.append(f"max_risk_per_trade must be between 0 and 0.05 (5%), got {self.max_risk_per_trade}")
        
        if not 0 < self.max_position_size <= 1.0:
            errors.append(f"max_position_size must be between 0 and 1.0 (100%), got {self.max_position_size}")
        
        if not 0 < self.max_portfolio_exposure <= 1.0:
            errors.append(f"max_portfolio_exposure must be between 0 and 1.0 (100%), got {self.max_portfolio_exposure}")
        
        # Validate portfolio value
        if self.portfolio_value <= 0:
            errors.append(f"portfolio_value must be positive, got {self.portfolio_value}")
        
        # Validate symbols
        if not self.symbols:
            errors.append("symbols list cannot be empty")
        
        # Validate API keys for non-analysis modes
        if self.mode in ['paper', 'live']:
            if not self.alpaca_api_key or not self.alpaca_secret_key:
                errors.append(f"Alpaca API keys required for {self.mode} mode")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Don't include API keys in serialization
        result.pop('anthropic_api_key', None)
        result.pop('alpaca_api_key', None)
        result.pop('alpaca_secret_key', None)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingConfig':
        """Create from dictionary."""
        return cls(**data)
