"""Professional trading agent with advanced indicators."""

from typing import Optional
import logging

from auronai.agents.trading_agent import TradingAgent
from auronai.core.models import TradingConfig
from auronai.indicators.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class TradingAgentPro(TradingAgent):
    """
    Professional trading agent with 15+ technical indicators.
    
    Extends the basic TradingAgent to use all advanced indicators including:
    - Stochastic Oscillator (%K, %D)
    - ATR (Average True Range)
    - OBV (On-Balance Volume)
    - Williams %R
    - CCI (Commodity Channel Index)
    - ROC (Rate of Change)
    
    Uses the same workflow as the basic version but with enhanced
    signal generation based on more comprehensive technical analysis.
    
    **Validates: Requirements 1.5, 1.6, 1.7, 1.8**
    """
    
    def __init__(
        self,
        mode: str = "analysis",
        config: Optional[TradingConfig] = None
    ):
        """
        Initialize professional trading agent.
        
        Args:
            mode: Trading mode - "analysis", "paper", or "live"
            config: Trading configuration (uses defaults if None)
            
        Raises:
            ValueError: If mode is invalid
        """
        # Call parent constructor
        super().__init__(mode=mode, config=config)
        
        # Override indicators with advanced mode enabled
        self.indicators = TechnicalIndicators(advanced_mode=True)
        
        logger.info(f"TradingAgentPro initialized in {mode} mode with 15+ indicators")
