"""Risk management module implementing Kelly Criterion and position sizing."""

from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Risk manager for calculating position sizes, stop losses, and enforcing risk limits.
    
    Uses Kelly Criterion for optimal position sizing and ATR-based dynamic stops.
    Enforces strict risk limits to protect capital.
    """
    
    def __init__(
        self,
        portfolio_value: float,
        max_risk_per_trade: float = 0.02,
        max_position_size: float = 0.20,
        max_portfolio_exposure: float = 0.80,
    ):
        """
        Initialize risk manager with portfolio value and risk parameters.
        
        Args:
            portfolio_value: Total portfolio value in USD
            max_risk_per_trade: Maximum risk per trade as decimal (default 0.02 = 2%)
            max_position_size: Maximum position size as fraction of portfolio (default 0.20 = 20%)
            max_portfolio_exposure: Maximum total portfolio exposure (default 0.80 = 80%)
            
        Raises:
            ValueError: If any parameter is invalid
        """
        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")
        if not 0 < max_risk_per_trade <= 1:
            raise ValueError("max_risk_per_trade must be between 0 and 1")
        if not 0 < max_position_size <= 1:
            raise ValueError("max_position_size must be between 0 and 1")
        if not 0 < max_portfolio_exposure <= 1:
            raise ValueError("max_portfolio_exposure must be between 0 and 1")
            
        self.portfolio_value = portfolio_value
        self.max_risk_per_trade = max_risk_per_trade
        self.max_position_size = max_position_size
        self.max_portfolio_exposure = max_portfolio_exposure
        
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        win_probability: float = 0.5,
        rr_ratio: float = 2.0,
    ) -> int:
        """
        Calculate optimal position size using Kelly Criterion.
        
        Kelly Criterion formula: f = (p * rr - (1 - p)) / rr
        where:
        - f = fraction of capital to risk
        - p = win probability
        - rr = risk-reward ratio
        
        Position size: shares = (portfolio_value * kelly_fraction) / (entry_price - stop_loss)
        
        Args:
            entry_price: Planned entry price per share
            stop_loss: Stop loss price per share
            win_probability: Probability of winning trade (0-1, default 0.5)
            rr_ratio: Risk-reward ratio (default 2.0)
            
        Returns:
            Number of shares to buy (integer), 0 if insufficient capital or invalid inputs
        """
        # Validate inputs
        if entry_price <= 0 or stop_loss <= 0:
            logger.warning("Invalid entry_price or stop_loss: must be positive")
            return 0
            
        if not 0 <= win_probability <= 1:
            logger.warning(f"Invalid win_probability {win_probability}: must be between 0 and 1")
            return 0
            
        if rr_ratio <= 0:
            logger.warning(f"Invalid rr_ratio {rr_ratio}: must be positive")
            return 0
            
        # For long positions, stop loss must be below entry
        if stop_loss >= entry_price:
            logger.warning(
                f"Invalid stop loss {stop_loss} for long position with entry {entry_price}: "
                "stop must be below entry"
            )
            return 0
            
        # Calculate Kelly fraction
        # f = (p * rr - (1 - p)) / rr
        kelly_fraction = (win_probability * rr_ratio - (1 - win_probability)) / rr_ratio
        
        # Kelly can be negative (suggests not taking the trade)
        if kelly_fraction <= 0:
            logger.info(
                f"Kelly Criterion suggests not taking trade: "
                f"kelly_fraction={kelly_fraction:.4f}"
            )
            return 0
            
        # Cap Kelly fraction at max_risk_per_trade (never risk more than limit)
        risk_fraction = min(kelly_fraction, self.max_risk_per_trade)
        
        # Calculate dollar amount to risk
        risk_amount = self.portfolio_value * risk_fraction
        
        # Calculate risk per share
        risk_per_share = entry_price - stop_loss
        
        # Calculate position size in shares
        shares = risk_amount / risk_per_share
        
        # Round down to integer shares
        shares = int(shares)
        
        # Validate against max position size limit
        max_shares_by_position_limit = self.get_max_shares(entry_price)
        if shares > max_shares_by_position_limit:
            logger.info(
                f"Position size {shares} exceeds max position limit, "
                f"reducing to {max_shares_by_position_limit}"
            )
            shares = max_shares_by_position_limit
            
        # Final validation
        if shares <= 0:
            logger.warning("Calculated position size is 0 or negative")
            return 0
            
        return shares
        
    def calculate_stop_loss(
        self, entry_price: float, atr: float, direction: str = "long"
    ) -> float:
        """
        Calculate dynamic stop loss based on ATR (Average True Range).
        
        For long positions: stop_loss = entry_price - (2 * ATR)
        For short positions: stop_loss = entry_price + (2 * ATR)
        
        Args:
            entry_price: Entry price per share
            atr: Average True Range value
            direction: Trade direction, "long" or "short" (default "long")
            
        Returns:
            Stop loss price, or None if inputs are invalid
        """
        if entry_price <= 0:
            logger.warning(f"Invalid entry_price {entry_price}: must be positive")
            return None
            
        if atr <= 0:
            logger.warning(f"Invalid ATR {atr}: must be positive")
            return None
            
        direction = direction.lower()
        if direction not in ["long", "short"]:
            logger.warning(f"Invalid direction {direction}: must be 'long' or 'short'")
            return None
            
        if direction == "long":
            stop_loss = entry_price - (2 * atr)
            # Ensure stop loss is positive
            if stop_loss <= 0:
                logger.warning(
                    f"Calculated stop loss {stop_loss} is non-positive for long position"
                )
                # Use a minimum stop loss of 1% below entry
                stop_loss = entry_price * 0.99
        else:  # short
            stop_loss = entry_price + (2 * atr)
            
        return round(stop_loss, 2)
        
    def calculate_take_profit(
        self, entry_price: float, stop_loss: float, rr_ratio: float = 2.0
    ) -> float:
        """
        Calculate take profit level based on risk-reward ratio.
        
        For long positions: take_profit = entry + (entry - stop) * rr_ratio
        For short positions: take_profit = entry - (stop - entry) * rr_ratio
        
        Args:
            entry_price: Entry price per share
            stop_loss: Stop loss price per share
            rr_ratio: Risk-reward ratio (default 2.0 for 2:1 reward:risk)
            
        Returns:
            Take profit price, or None if inputs are invalid
        """
        if entry_price <= 0 or stop_loss <= 0:
            logger.warning("Invalid entry_price or stop_loss: must be positive")
            return None
            
        if rr_ratio < 1.5:
            logger.warning(
                f"Risk-reward ratio {rr_ratio} is below minimum 1.5:1, using 1.5"
            )
            rr_ratio = 1.5
            
        # Determine direction based on stop loss position
        if stop_loss < entry_price:
            # Long position
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * rr_ratio)
        else:
            # Short position
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * rr_ratio)
            
            # Ensure take profit is positive for shorts
            if take_profit <= 0:
                logger.warning(
                    f"Calculated take profit {take_profit} is non-positive for short position"
                )
                return None
                
        return round(take_profit, 2)
        
    def validate_trade(
        self, position_size: int, entry_price: float, current_exposure: float = 0.0
    ) -> Tuple[bool, str]:
        """
        Validate if trade meets all risk criteria.
        
        Checks:
        1. Position size is positive
        2. Position value doesn't exceed max_position_size limit
        3. Total portfolio exposure doesn't exceed max_portfolio_exposure limit
        
        Args:
            position_size: Number of shares to trade
            entry_price: Entry price per share
            current_exposure: Current portfolio exposure as fraction (0-1)
            
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        if position_size <= 0:
            return False, "Position size must be positive"
            
        if entry_price <= 0:
            return False, "Entry price must be positive"
            
        if not 0 <= current_exposure <= 1:
            return False, f"Invalid current_exposure {current_exposure}: must be between 0 and 1"
            
        # Check position size limit
        position_value = position_size * entry_price
        position_fraction = position_value / self.portfolio_value
        
        if position_fraction > self.max_position_size:
            return False, (
                f"Position size {position_fraction:.2%} exceeds maximum "
                f"{self.max_position_size:.2%} of portfolio"
            )
            
        # Check total portfolio exposure
        new_exposure = current_exposure + position_fraction
        if new_exposure > self.max_portfolio_exposure:
            return False, (
                f"Total exposure {new_exposure:.2%} would exceed maximum "
                f"{self.max_portfolio_exposure:.2%}"
            )
            
        return True, "Trade validated successfully"
        
    def get_max_shares(self, price: float) -> int:
        """
        Calculate maximum shares allowed based on position size limit.
        
        Args:
            price: Price per share
            
        Returns:
            Maximum number of shares allowed
        """
        if price <= 0:
            logger.warning(f"Invalid price {price}: must be positive")
            return 0
            
        max_position_value = self.portfolio_value * self.max_position_size
        max_shares = int(max_position_value / price)
        
        return max_shares
