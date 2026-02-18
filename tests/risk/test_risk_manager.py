"""Unit tests for RiskManager."""

import pytest
from src.auronai.risk import RiskManager


class TestRiskManagerInitialization:
    """Test RiskManager initialization and validation."""
    
    def test_valid_initialization(self):
        """RiskManager should initialize with valid parameters."""
        rm = RiskManager(
            portfolio_value=10000.0,
            max_risk_per_trade=0.02,
            max_position_size=0.20,
            max_portfolio_exposure=0.80,
        )
        
        assert rm.portfolio_value == 10000.0
        assert rm.max_risk_per_trade == 0.02
        assert rm.max_position_size == 0.20
        assert rm.max_portfolio_exposure == 0.80
        
    def test_invalid_portfolio_value(self):
        """RiskManager should reject non-positive portfolio value."""
        with pytest.raises(ValueError, match="Portfolio value must be positive"):
            RiskManager(portfolio_value=0)
            
        with pytest.raises(ValueError, match="Portfolio value must be positive"):
            RiskManager(portfolio_value=-1000)
            
    def test_invalid_risk_parameters(self):
        """RiskManager should reject invalid risk parameters."""
        with pytest.raises(ValueError, match="max_risk_per_trade"):
            RiskManager(portfolio_value=10000, max_risk_per_trade=0)
            
        with pytest.raises(ValueError, match="max_risk_per_trade"):
            RiskManager(portfolio_value=10000, max_risk_per_trade=1.5)
            
        with pytest.raises(ValueError, match="max_position_size"):
            RiskManager(portfolio_value=10000, max_position_size=0)
            
        with pytest.raises(ValueError, match="max_portfolio_exposure"):
            RiskManager(portfolio_value=10000, max_portfolio_exposure=1.5)


class TestPositionSizing:
    """Test position size calculation with Kelly Criterion."""
    
    def test_basic_position_sizing(self):
        """Position sizing should work with valid inputs."""
        rm = RiskManager(portfolio_value=10000.0, max_risk_per_trade=0.02)
        
        # Entry at $100, stop at $90 (10% risk per share)
        # With 50% win prob and 2:1 R/R, Kelly = (0.5*2 - 0.5)/2 = 0.25
        # Capped at 2% = $200 risk / $10 per share = 20 shares
        position_size = rm.calculate_position_size(
            entry_price=100.0,
            stop_loss=90.0,
            win_probability=0.5,
            rr_ratio=2.0,
        )
        
        assert position_size == 20
        
    def test_insufficient_capital(self):
        """Position sizing should return 0 with insufficient capital."""
        rm = RiskManager(portfolio_value=100.0)  # Small portfolio
        
        # Entry at $1000, stop at $900 - too expensive
        position_size = rm.calculate_position_size(
            entry_price=1000.0,
            stop_loss=900.0,
            win_probability=0.5,
            rr_ratio=2.0,
        )
        
        assert position_size == 0
        
    def test_negative_kelly(self):
        """Position sizing should return 0 when Kelly is negative."""
        rm = RiskManager(portfolio_value=10000.0)
        
        # Low win probability with low R/R gives negative Kelly
        position_size = rm.calculate_position_size(
            entry_price=100.0,
            stop_loss=90.0,
            win_probability=0.3,  # Low win rate
            rr_ratio=1.5,  # Low R/R
        )
        
        assert position_size == 0
        
    def test_invalid_stop_loss(self):
        """Position sizing should return 0 with invalid stop loss."""
        rm = RiskManager(portfolio_value=10000.0)
        
        # Stop loss above entry for long position
        position_size = rm.calculate_position_size(
            entry_price=100.0,
            stop_loss=110.0,  # Invalid for long
            win_probability=0.5,
            rr_ratio=2.0,
        )
        
        assert position_size == 0
        
    def test_position_size_respects_max_position_limit(self):
        """Position sizing should not exceed max position size limit."""
        rm = RiskManager(
            portfolio_value=10000.0,
            max_risk_per_trade=0.50,  # High risk allowed
            max_position_size=0.10,  # But position limited to 10%
        )
        
        # This would normally give a large position, but should be capped
        position_size = rm.calculate_position_size(
            entry_price=10.0,
            stop_loss=9.0,
            win_probability=0.8,
            rr_ratio=3.0,
        )
        
        # Max position = 10% of $10000 = $1000 / $10 = 100 shares
        assert position_size <= 100


class TestStopLossCalculation:
    """Test ATR-based stop loss calculation."""
    
    def test_long_position_stop_loss(self):
        """Stop loss for long should be entry - 2*ATR."""
        rm = RiskManager(portfolio_value=10000.0)
        
        stop_loss = rm.calculate_stop_loss(
            entry_price=100.0,
            atr=2.5,
            direction="long",
        )
        
        # Expected: 100 - (2 * 2.5) = 95.0
        assert stop_loss == 95.0
        
    def test_short_position_stop_loss(self):
        """Stop loss for short should be entry + 2*ATR."""
        rm = RiskManager(portfolio_value=10000.0)
        
        stop_loss = rm.calculate_stop_loss(
            entry_price=100.0,
            atr=2.5,
            direction="short",
        )
        
        # Expected: 100 + (2 * 2.5) = 105.0
        assert stop_loss == 105.0
        
    def test_stop_loss_minimum_for_long(self):
        """Stop loss should have minimum of 1% below entry for longs."""
        rm = RiskManager(portfolio_value=10000.0)
        
        # Very high ATR that would make stop negative
        stop_loss = rm.calculate_stop_loss(
            entry_price=10.0,
            atr=10.0,  # 2*ATR = 20, would give negative stop
            direction="long",
        )
        
        # Should use 1% minimum: 10 * 0.99 = 9.9
        assert stop_loss == 9.9
        
    def test_invalid_direction(self):
        """Stop loss should return None for invalid direction."""
        rm = RiskManager(portfolio_value=10000.0)
        
        stop_loss = rm.calculate_stop_loss(
            entry_price=100.0,
            atr=2.5,
            direction="sideways",  # Invalid
        )
        
        assert stop_loss is None


class TestTakeProfitCalculation:
    """Test risk-reward based take profit calculation."""
    
    def test_long_position_take_profit(self):
        """Take profit for long should respect R/R ratio."""
        rm = RiskManager(portfolio_value=10000.0)
        
        take_profit = rm.calculate_take_profit(
            entry_price=100.0,
            stop_loss=95.0,  # $5 risk
            rr_ratio=2.0,
        )
        
        # Expected: 100 + (5 * 2) = 110.0
        assert take_profit == 110.0
        
    def test_short_position_take_profit(self):
        """Take profit for short should respect R/R ratio."""
        rm = RiskManager(portfolio_value=10000.0)
        
        take_profit = rm.calculate_take_profit(
            entry_price=100.0,
            stop_loss=105.0,  # $5 risk
            rr_ratio=2.0,
        )
        
        # Expected: 100 - (5 * 2) = 90.0
        assert take_profit == 90.0
        
    def test_minimum_rr_ratio_enforced(self):
        """R/R ratio below 1.5 should be adjusted to 1.5."""
        rm = RiskManager(portfolio_value=10000.0)
        
        take_profit = rm.calculate_take_profit(
            entry_price=100.0,
            stop_loss=95.0,  # $5 risk
            rr_ratio=1.0,  # Below minimum
        )
        
        # Should use 1.5: 100 + (5 * 1.5) = 107.5
        assert take_profit == 107.5


class TestTradeValidation:
    """Test trade validation against risk limits."""
    
    def test_valid_trade(self):
        """Valid trade should pass validation."""
        rm = RiskManager(
            portfolio_value=10000.0,
            max_position_size=0.20,
            max_portfolio_exposure=0.80,
        )
        
        # Position: 10 shares * $100 = $1000 (10% of portfolio)
        is_valid, message = rm.validate_trade(
            position_size=10,
            entry_price=100.0,
            current_exposure=0.0,
        )
        
        assert is_valid
        assert "successfully" in message.lower()
        
    def test_position_size_too_large(self):
        """Trade exceeding position size limit should be rejected."""
        rm = RiskManager(
            portfolio_value=10000.0,
            max_position_size=0.10,  # 10% max
        )
        
        # Position: 20 shares * $100 = $2000 (20% of portfolio)
        is_valid, message = rm.validate_trade(
            position_size=20,
            entry_price=100.0,
            current_exposure=0.0,
        )
        
        assert not is_valid
        assert "exceeds maximum" in message.lower()
        
    def test_total_exposure_too_high(self):
        """Trade exceeding total exposure limit should be rejected."""
        rm = RiskManager(
            portfolio_value=10000.0,
            max_portfolio_exposure=0.80,  # 80% max
        )
        
        # Position: 10 shares * $100 = $1000 (10% of portfolio)
        # Current exposure: 75%
        # New total: 85% > 80%
        is_valid, message = rm.validate_trade(
            position_size=10,
            entry_price=100.0,
            current_exposure=0.75,
        )
        
        assert not is_valid
        assert "exposure" in message.lower()
        
    def test_invalid_position_size(self):
        """Zero or negative position size should be rejected."""
        rm = RiskManager(portfolio_value=10000.0)
        
        is_valid, message = rm.validate_trade(
            position_size=0,
            entry_price=100.0,
            current_exposure=0.0,
        )
        
        assert not is_valid
        assert "positive" in message.lower()


class TestMaxSharesCalculation:
    """Test maximum shares calculation."""
    
    def test_max_shares_calculation(self):
        """Max shares should respect position size limit."""
        rm = RiskManager(
            portfolio_value=10000.0,
            max_position_size=0.20,  # 20% max
        )
        
        # Max position value: $10000 * 0.20 = $2000
        # At $50/share: 2000 / 50 = 40 shares
        max_shares = rm.get_max_shares(price=50.0)
        
        assert max_shares == 40
        
    def test_max_shares_with_expensive_stock(self):
        """Max shares should handle expensive stocks."""
        rm = RiskManager(
            portfolio_value=10000.0,
            max_position_size=0.10,  # 10% max
        )
        
        # Max position value: $10000 * 0.10 = $1000
        # At $500/share: 1000 / 500 = 2 shares
        max_shares = rm.get_max_shares(price=500.0)
        
        assert max_shares == 2
        
    def test_max_shares_with_invalid_price(self):
        """Max shares should return 0 for invalid price."""
        rm = RiskManager(portfolio_value=10000.0)
        
        max_shares = rm.get_max_shares(price=0)
        assert max_shares == 0
        
        max_shares = rm.get_max_shares(price=-10)
        assert max_shares == 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_win_probability(self):
        """Position sizing should handle 0% win probability."""
        rm = RiskManager(portfolio_value=10000.0)
        
        position_size = rm.calculate_position_size(
            entry_price=100.0,
            stop_loss=90.0,
            win_probability=0.0,
            rr_ratio=2.0,
        )
        
        # Kelly will be negative, should return 0
        assert position_size == 0
        
    def test_very_high_win_probability(self):
        """Position sizing should handle very high win probability."""
        rm = RiskManager(portfolio_value=10000.0, max_risk_per_trade=0.02)
        
        position_size = rm.calculate_position_size(
            entry_price=100.0,
            stop_loss=90.0,
            win_probability=0.9,
            rr_ratio=3.0,
        )
        
        # Should still be capped by max_risk_per_trade
        assert position_size > 0
        
        # Verify risk doesn't exceed limit
        risk_per_share = 100.0 - 90.0
        total_risk = position_size * risk_per_share
        risk_fraction = total_risk / 10000.0
        
        assert risk_fraction <= 0.02 + 0.0001  # Small tolerance
        
    def test_very_small_atr(self):
        """Stop loss calculation should handle very small ATR."""
        rm = RiskManager(portfolio_value=10000.0)
        
        stop_loss = rm.calculate_stop_loss(
            entry_price=100.0,
            atr=0.01,  # Very small
            direction="long",
        )
        
        # Should still calculate: 100 - (2 * 0.01) = 99.98
        assert stop_loss == 99.98
        
    def test_rounding_consistency(self):
        """Results should be consistently rounded to 2 decimals."""
        rm = RiskManager(portfolio_value=10000.0)
        
        stop_loss = rm.calculate_stop_loss(
            entry_price=100.123,
            atr=2.567,
            direction="long",
        )
        
        # Should be rounded to 2 decimals
        assert stop_loss == round(100.123 - (2 * 2.567), 2)
        
        take_profit = rm.calculate_take_profit(
            entry_price=100.123,
            stop_loss=95.456,
            rr_ratio=2.0,
        )
        
        # Should be rounded to 2 decimals
        assert isinstance(take_profit, float)
        assert len(str(take_profit).split('.')[-1]) <= 2
