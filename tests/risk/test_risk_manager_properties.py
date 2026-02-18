"""Property-based tests for RiskManager using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, assume
from src.auronai.risk import RiskManager


# Strategy for generating valid portfolio values
portfolio_values = st.floats(min_value=1000.0, max_value=1_000_000.0)

# Strategy for generating valid risk parameters
risk_percentages = st.floats(min_value=0.001, max_value=0.1)  # 0.1% to 10%
position_sizes = st.floats(min_value=0.05, max_value=0.5)  # 5% to 50%
exposure_limits = st.floats(min_value=0.5, max_value=1.0)  # 50% to 100%

# Strategy for generating valid prices
prices = st.floats(min_value=1.0, max_value=1000.0)

# Strategy for generating valid ATR values
atr_values = st.floats(min_value=0.1, max_value=50.0)

# Strategy for generating valid probabilities
probabilities = st.floats(min_value=0.1, max_value=0.9)

# Strategy for generating valid risk-reward ratios
rr_ratios = st.floats(min_value=1.5, max_value=5.0)


class TestRiskLimitsEnforcement:
    """
    Property 5: Risk Limits Enforcement
    
    For any position size calculation, the result must satisfy:
    - risk_per_trade <= max_risk_per_trade
    - position_value <= max_position_size * portfolio_value
    - total_exposure <= max_portfolio_exposure
    
    Validates: Requirements 3.2, 3.3, 3.6, 3.7, 3.10
    """
    
    @given(
        portfolio_value=portfolio_values,
        max_risk=risk_percentages,
        max_position=position_sizes,
        max_exposure=exposure_limits,
        entry_price=prices,
        win_prob=probabilities,
        rr_ratio=rr_ratios,
    )
    def test_position_size_respects_risk_limits(
        self,
        portfolio_value,
        max_risk,
        max_position,
        max_exposure,
        entry_price,
        win_prob,
        rr_ratio,
    ):
        """Position size calculation must respect all risk limits."""
        # Create risk manager with specified limits
        risk_manager = RiskManager(
            portfolio_value=portfolio_value,
            max_risk_per_trade=max_risk,
            max_position_size=max_position,
            max_portfolio_exposure=max_exposure,
        )
        
        # Calculate stop loss (10% below entry for testing)
        stop_loss = entry_price * 0.90
        
        # Calculate position size
        position_size = risk_manager.calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            win_probability=win_prob,
            rr_ratio=rr_ratio,
        )
        
        # If position size is 0, that's valid (insufficient capital or Kelly says no)
        if position_size == 0:
            return
            
        # Calculate actual risk and position value
        risk_per_share = entry_price - stop_loss
        actual_risk = position_size * risk_per_share
        actual_risk_fraction = actual_risk / portfolio_value
        
        position_value = position_size * entry_price
        position_fraction = position_value / portfolio_value
        
        # Property: Risk per trade must not exceed max_risk_per_trade
        assert actual_risk_fraction <= max_risk + 0.0001, (  # Small tolerance for rounding
            f"Risk {actual_risk_fraction:.4f} exceeds max {max_risk:.4f}"
        )
        
        # Property: Position size must not exceed max_position_size
        assert position_fraction <= max_position + 0.0001, (
            f"Position {position_fraction:.4f} exceeds max {max_position:.4f}"
        )
        
    @given(
        portfolio_value=portfolio_values,
        max_position=position_sizes,
        entry_price=prices,
        position_size=st.integers(min_value=1, max_value=10000),
        current_exposure=st.floats(min_value=0.0, max_value=0.8),
    )
    def test_validate_trade_enforces_position_limit(
        self, portfolio_value, max_position, entry_price, position_size, current_exposure
    ):
        """validate_trade must reject trades exceeding position size limit."""
        risk_manager = RiskManager(
            portfolio_value=portfolio_value,
            max_position_size=max_position,
        )
        
        is_valid, message = risk_manager.validate_trade(
            position_size=position_size,
            entry_price=entry_price,
            current_exposure=current_exposure,
        )
        
        # Calculate actual position fraction
        position_value = position_size * entry_price
        position_fraction = position_value / portfolio_value
        
        # Property: If position exceeds limit, trade must be invalid
        if position_fraction > max_position:
            assert not is_valid, (
                f"Trade should be invalid: position {position_fraction:.4f} > "
                f"max {max_position:.4f}"
            )
            assert "exceeds maximum" in message.lower()
            
    @given(
        portfolio_value=portfolio_values,
        max_exposure=exposure_limits,
        entry_price=prices,
        position_size=st.integers(min_value=1, max_value=1000),
        current_exposure=st.floats(min_value=0.0, max_value=0.95),
    )
    def test_validate_trade_enforces_exposure_limit(
        self, portfolio_value, max_exposure, entry_price, position_size, current_exposure
    ):
        """validate_trade must reject trades exceeding total exposure limit."""
        risk_manager = RiskManager(
            portfolio_value=portfolio_value,
            max_portfolio_exposure=max_exposure,
        )
        
        is_valid, message = risk_manager.validate_trade(
            position_size=position_size,
            entry_price=entry_price,
            current_exposure=current_exposure,
        )
        
        # Calculate new total exposure
        position_value = position_size * entry_price
        position_fraction = position_value / portfolio_value
        new_exposure = current_exposure + position_fraction
        
        # Property: If total exposure exceeds limit, trade must be invalid
        # Note: Position size limit is checked first, so we only check exposure
        # if position size is within limits
        position_value = position_size * entry_price
        position_fraction = position_value / portfolio_value
        
        if new_exposure > max_exposure and position_fraction <= risk_manager.max_position_size:
            assert not is_valid, (
                f"Trade should be invalid: exposure {new_exposure:.4f} > "
                f"max {max_exposure:.4f}"
            )
            assert "exposure" in message.lower()
            
    @given(
        portfolio_value=portfolio_values,
        max_position=position_sizes,
        price=prices,
    )
    def test_get_max_shares_respects_position_limit(
        self, portfolio_value, max_position, price
    ):
        """get_max_shares must return shares that don't exceed position limit."""
        risk_manager = RiskManager(
            portfolio_value=portfolio_value,
            max_position_size=max_position,
        )
        
        max_shares = risk_manager.get_max_shares(price)
        
        # Property: Max shares value must not exceed position limit
        if max_shares > 0:
            max_value = max_shares * price
            max_fraction = max_value / portfolio_value
            
            assert max_fraction <= max_position + 0.0001, (
                f"Max shares value {max_fraction:.4f} exceeds limit {max_position:.4f}"
            )


class TestKellyCriterionPositionSizing:
    """
    Property 6: Kelly Criterion Position Sizing
    
    For any valid win probability and risk-reward ratio, position size calculated
    using Kelly Criterion should be:
    size = (portfolio_value * kelly_fraction) / (entry_price - stop_loss)
    where kelly_fraction = (p * rr - (1 - p)) / rr
    
    Validates: Requirements 3.1
    """
    
    @given(
        portfolio_value=portfolio_values,
        entry_price=prices,
        win_prob=probabilities,
        rr_ratio=rr_ratios,
    )
    def test_kelly_criterion_formula(
        self, portfolio_value, entry_price, win_prob, rr_ratio
    ):
        """Position sizing must follow Kelly Criterion formula."""
        # Use default risk limits
        risk_manager = RiskManager(portfolio_value=portfolio_value)
        
        # Calculate stop loss (10% below entry)
        stop_loss = entry_price * 0.90
        
        # Calculate position size
        position_size = risk_manager.calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            win_probability=win_prob,
            rr_ratio=rr_ratio,
        )
        
        # Calculate expected Kelly fraction
        kelly_fraction = (win_prob * rr_ratio - (1 - win_prob)) / rr_ratio
        
        # If Kelly is negative or zero, position should be 0
        if kelly_fraction <= 0:
            assert position_size == 0, "Position should be 0 when Kelly is non-positive"
            return
            
        # Cap Kelly at max_risk_per_trade
        capped_kelly = min(kelly_fraction, risk_manager.max_risk_per_trade)
        
        # Calculate expected position size
        risk_amount = portfolio_value * capped_kelly
        risk_per_share = entry_price - stop_loss
        expected_shares = int(risk_amount / risk_per_share)
        
        # Also check against max position size limit
        max_shares_by_limit = risk_manager.get_max_shares(entry_price)
        expected_shares = min(expected_shares, max_shares_by_limit)
        
        # Property: Calculated position size should match Kelly formula
        assert position_size == expected_shares, (
            f"Position size {position_size} doesn't match Kelly formula {expected_shares}"
        )


class TestATRBasedStopLoss:
    """
    Property 7: ATR-Based Stop Loss
    
    For any long position, stop loss should equal entry_price - (2 * ATR)
    For short positions, stop loss should equal entry_price + (2 * ATR)
    
    Validates: Requirements 3.4
    """
    
    @given(
        entry_price=prices,
        atr=atr_values,
    )
    def test_long_position_stop_loss(self, entry_price, atr):
        """Stop loss for long positions must be entry - 2*ATR."""
        risk_manager = RiskManager(portfolio_value=10000.0)
        
        stop_loss = risk_manager.calculate_stop_loss(
            entry_price=entry_price,
            atr=atr,
            direction="long",
        )
        
        # Property: Stop loss should be entry - 2*ATR
        expected_stop = entry_price - (2 * atr)
        
        # If expected stop is negative, implementation uses 1% below entry as minimum
        if expected_stop <= 0:
            expected_stop = entry_price * 0.99
            
        expected_stop = round(expected_stop, 2)
        
        assert stop_loss == expected_stop, (
            f"Long stop loss {stop_loss} doesn't match expected {expected_stop}"
        )
        
    @given(
        entry_price=prices,
        atr=atr_values,
    )
    def test_short_position_stop_loss(self, entry_price, atr):
        """Stop loss for short positions must be entry + 2*ATR."""
        risk_manager = RiskManager(portfolio_value=10000.0)
        
        stop_loss = risk_manager.calculate_stop_loss(
            entry_price=entry_price,
            atr=atr,
            direction="short",
        )
        
        # Property: Stop loss should be entry + 2*ATR
        expected_stop = round(entry_price + (2 * atr), 2)
        
        assert stop_loss == expected_stop, (
            f"Short stop loss {stop_loss} doesn't match expected {expected_stop}"
        )


class TestRiskRewardRatioEnforcement:
    """
    Property 8: Risk-Reward Ratio Enforcement
    
    For any trade plan, the risk-reward ratio should be at least 2:1,
    meaning (take_profit - entry) / (entry - stop_loss) >= 2.0 for long positions
    
    Validates: Requirements 3.5
    """
    
    @given(
        entry_price=prices,
        rr_ratio=rr_ratios,
    )
    def test_take_profit_respects_rr_ratio_long(self, entry_price, rr_ratio):
        """Take profit for long positions must respect risk-reward ratio."""
        risk_manager = RiskManager(portfolio_value=10000.0)
        
        # Calculate stop loss (10% below entry)
        stop_loss = entry_price * 0.90
        
        take_profit = risk_manager.calculate_take_profit(
            entry_price=entry_price,
            stop_loss=stop_loss,
            rr_ratio=rr_ratio,
        )
        
        # Property: Take profit should give at least the specified R/R ratio
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        actual_rr = reward / risk
        
        # Allow tolerance for rounding (0.05 instead of 0.01 due to 2-decimal rounding)
        assert actual_rr >= rr_ratio - 0.05, (
            f"R/R ratio {actual_rr:.2f} is less than required {rr_ratio:.2f}"
        )
        
    @given(
        entry_price=prices,
        rr_ratio=rr_ratios,
    )
    def test_take_profit_respects_rr_ratio_short(self, entry_price, rr_ratio):
        """Take profit for short positions must respect risk-reward ratio."""
        risk_manager = RiskManager(portfolio_value=10000.0)
        
        # Calculate stop loss (10% above entry for short)
        stop_loss = entry_price * 1.10
        
        take_profit = risk_manager.calculate_take_profit(
            entry_price=entry_price,
            stop_loss=stop_loss,
            rr_ratio=rr_ratio,
        )
        
        # Skip if take profit is None (can happen for shorts with high stop loss)
        if take_profit is None:
            return
            
        # Property: Take profit should give at least the specified R/R ratio
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
        actual_rr = reward / risk
        
        # Allow tolerance for rounding (0.05 instead of 0.01 due to 2-decimal rounding)
        assert actual_rr >= rr_ratio - 0.05, (
            f"R/R ratio {actual_rr:.2f} is less than required {rr_ratio:.2f}"
        )
        
    @given(
        entry_price=prices,
        rr_ratio=st.floats(min_value=0.5, max_value=1.4),  # Below minimum
    )
    def test_minimum_rr_ratio_enforced(self, entry_price, rr_ratio):
        """Risk-reward ratio below 1.5:1 should be adjusted to minimum."""
        risk_manager = RiskManager(portfolio_value=10000.0)
        
        stop_loss = entry_price * 0.90
        
        take_profit = risk_manager.calculate_take_profit(
            entry_price=entry_price,
            stop_loss=stop_loss,
            rr_ratio=rr_ratio,
        )
        
        # Property: Actual R/R should be at least 1.5:1 even if lower was requested
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        actual_rr = reward / risk
        
        assert actual_rr >= 1.5 - 0.05, (  # Tolerance for rounding
            f"R/R ratio {actual_rr:.2f} is below minimum 1.5:1"
        )
