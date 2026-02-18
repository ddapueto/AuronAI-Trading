"""Property-based tests for core data models.

**Validates: Requirements 2.5, 6.2**
"""

from datetime import datetime, timedelta
from hypothesis import given, strategies as st
import pytest

from auronai.core.models import (
    MarketData,
    TechnicalIndicators,
    TradingSignal,
    TradePlan,
    BacktestResult,
    TradingConfig
)


# Strategies for generating test data
@st.composite
def valid_ohlc_data(draw):
    """Generate valid OHLC data where high >= max(open, close) and low <= min(open, close)."""
    # Generate base price
    base_price = draw(st.floats(min_value=1.0, max_value=10000.0))
    
    # Generate open and close around base price
    open_price = draw(st.floats(min_value=base_price * 0.95, max_value=base_price * 1.05))
    close_price = draw(st.floats(min_value=base_price * 0.95, max_value=base_price * 1.05))
    
    # Ensure high >= max(open, close)
    max_oc = max(open_price, close_price)
    high = draw(st.floats(min_value=max_oc, max_value=max_oc * 1.1))
    
    # Ensure low <= min(open, close)
    min_oc = min(open_price, close_price)
    low = draw(st.floats(min_value=min_oc * 0.9, max_value=min_oc))
    
    return open_price, high, low, close_price


@st.composite
def market_data_strategy(draw):
    """Generate valid MarketData instances."""
    symbol = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu',))))
    timestamp = draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31)))
    open_price, high, low, close = draw(valid_ohlc_data())
    volume = draw(st.integers(min_value=0, max_value=1_000_000_000))
    
    return MarketData(
        symbol=symbol,
        timestamp=timestamp,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume
    )


# Property 3: Market Data Validation
@given(market_data_strategy())
def test_property_market_data_validation(market_data):
    """
    **Property 3: Market Data Validation**
    
    For any valid MarketData instance, the validate() method should return True,
    and OHLC relationships must be valid:
    - high >= max(open, close)
    - low <= min(open, close)
    - volume >= 0
    - all prices > 0
    
    **Validates: Requirements 2.5, 6.2**
    """
    # The data should be valid
    assert market_data.validate(), f"Generated market data should be valid: {market_data}"
    
    # Verify OHLC relationships
    assert market_data.high >= max(market_data.open, market_data.close), \
        f"High ({market_data.high}) must be >= max(open={market_data.open}, close={market_data.close})"
    
    assert market_data.low <= min(market_data.open, market_data.close), \
        f"Low ({market_data.low}) must be <= min(open={market_data.open}, close={market_data.close})"
    
    # Verify volume is non-negative
    assert market_data.volume >= 0, f"Volume must be non-negative, got {market_data.volume}"
    
    # Verify all prices are positive
    assert market_data.open > 0, f"Open price must be positive, got {market_data.open}"
    assert market_data.high > 0, f"High price must be positive, got {market_data.high}"
    assert market_data.low > 0, f"Low price must be positive, got {market_data.low}"
    assert market_data.close > 0, f"Close price must be positive, got {market_data.close}"


@given(
    symbol=st.text(min_size=1, max_size=10),
    timestamp=st.datetimes(min_value=datetime(2020, 1, 1)),
    open_price=st.floats(min_value=0.01, max_value=10000.0),
    high=st.floats(min_value=0.01, max_value=10000.0),
    low=st.floats(min_value=0.01, max_value=10000.0),
    close=st.floats(min_value=0.01, max_value=10000.0),
    volume=st.integers(min_value=-1000, max_value=1_000_000_000)
)
def test_property_market_data_validation_detects_invalid(symbol, timestamp, open_price, high, low, close, volume):
    """
    **Property 3 (Inverse): Market Data Validation Detects Invalid Data**
    
    For any MarketData instance with invalid OHLC relationships or negative volume,
    the validate() method should return False.
    
    **Validates: Requirements 2.5, 6.2**
    """
    market_data = MarketData(
        symbol=symbol,
        timestamp=timestamp,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume
    )
    
    # Check if data is actually invalid
    is_invalid = (
        high < max(open_price, close) or
        low > min(open_price, close) or
        volume < 0 or
        any(v <= 0 for v in [open_price, high, low, close])
    )
    
    if is_invalid:
        assert not market_data.validate(), \
            f"Invalid market data should fail validation: {market_data}"


@given(
    action=st.sampled_from(["BUY", "SELL"]),
    position_size=st.integers(min_value=1, max_value=10000),
    entry_price=st.floats(min_value=1.0, max_value=1000.0),
    rr_ratio=st.floats(min_value=1.5, max_value=5.0)
)
def test_property_trade_plan_validation_valid_long(action, position_size, entry_price, rr_ratio):
    """
    **Property: Trade Plan Validation for Valid Plans**
    
    For any TradePlan with valid parameters (stop below entry for BUY, above for SELL,
    RR ratio >= 1.5), validate() should return (True, "Valid").
    
    **Validates: Requirements 3.4, 3.5**
    """
    if action == "BUY":
        stop_loss = entry_price * 0.95  # 5% below entry
        take_profit = entry_price + (entry_price - stop_loss) * rr_ratio
    else:  # SELL
        stop_loss = entry_price * 1.05  # 5% above entry
        take_profit = entry_price - (stop_loss - entry_price) * rr_ratio
    
    risk_amount = abs(entry_price - stop_loss) * position_size
    reward_amount = abs(take_profit - entry_price) * position_size
    
    trade_plan = TradePlan(
        symbol="TEST",
        action=action,
        position_size=position_size,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_amount=risk_amount,
        reward_amount=reward_amount,
        rr_ratio=rr_ratio
    )
    
    is_valid, message = trade_plan.validate()
    assert is_valid, f"Valid trade plan should pass validation: {message}"
    assert message == "Valid"


@given(
    action=st.sampled_from(["BUY", "SELL", "HOLD"]),
    confidence=st.floats(min_value=0.0, max_value=10.0),
    min_confidence=st.floats(min_value=5.0, max_value=9.0)
)
def test_property_trading_signal_actionable(action, confidence, min_confidence):
    """
    **Property: Trading Signal Actionability**
    
    For any TradingSignal, is_actionable() should return True if and only if:
    - action is "BUY" or "SELL" (not "HOLD")
    - confidence >= min_confidence threshold
    
    **Validates: Requirements 5.2**
    """
    signal = TradingSignal(
        symbol="TEST",
        timestamp=datetime.now(),
        action=action,
        confidence=confidence,
        strategy="test_strategy",
        bullish_signals=[],
        bearish_signals=[]
    )
    
    expected_actionable = (action in ["BUY", "SELL"]) and (confidence >= min_confidence)
    actual_actionable = signal.is_actionable(min_confidence=min_confidence)
    
    assert actual_actionable == expected_actionable, \
        f"Signal actionability mismatch: action={action}, confidence={confidence}, " \
        f"min_confidence={min_confidence}, expected={expected_actionable}, got={actual_actionable}"


@given(
    mode=st.sampled_from(['analysis', 'paper', 'live']),
    portfolio_value=st.floats(min_value=100.0, max_value=1_000_000.0),
    max_risk_per_trade=st.floats(min_value=0.001, max_value=0.05),
    max_position_size=st.floats(min_value=0.01, max_value=1.0),
    max_portfolio_exposure=st.floats(min_value=0.1, max_value=1.0)
)
def test_property_trading_config_validation_valid(
    mode, portfolio_value, max_risk_per_trade, max_position_size, max_portfolio_exposure
):
    """
    **Property: Trading Config Validation for Valid Configs**
    
    For any TradingConfig with valid parameters, validate() should return (True, []).
    
    **Validates: Requirements 9.4, 9.9**
    """
    config = TradingConfig(
        mode=mode,
        portfolio_value=portfolio_value,
        max_risk_per_trade=max_risk_per_trade,
        max_position_size=max_position_size,
        max_portfolio_exposure=max_portfolio_exposure,
        symbols=["AAPL", "MSFT"],
        # For paper/live modes, we'd need API keys, but we'll test analysis mode
        alpaca_api_key="test_key" if mode in ['paper', 'live'] else None,
        alpaca_secret_key="test_secret" if mode in ['paper', 'live'] else None
    )
    
    is_valid, errors = config.validate()
    
    if mode == 'analysis':
        # Analysis mode should always be valid with these parameters
        assert is_valid, f"Valid config should pass validation. Errors: {errors}"
        assert len(errors) == 0, f"Valid config should have no errors, got: {errors}"


def test_property_config_default_completeness():
    """
    **Property 20: Configuration Default Completeness**
    
    For any configuration parameter, if not explicitly set, a valid default value
    should be provided.
    
    **Validates: Requirements 9.3**
    """
    # Create config with no parameters
    config = TradingConfig()
    
    # All fields should have valid defaults
    assert config.mode == "analysis"
    assert config.portfolio_value == 10000.0
    assert config.max_risk_per_trade == 0.02
    assert config.max_position_size == 0.20
    assert config.max_portfolio_exposure == 0.80
    assert config.strategy == "swing_weekly"
    assert config.symbols == ["AAPL", "MSFT", "NVDA"]
    assert config.use_claude is True
    
    # Validate that defaults are valid
    is_valid, errors = config.validate()
    assert is_valid, f"Default config should be valid. Errors: {errors}"


# Property 23: Results Persistence Round-Trip
@given(market_data_strategy())
def test_property_market_data_json_roundtrip(market_data):
    """
    **Property 23: Results Persistence Round-Trip (MarketData)**
    
    For any MarketData instance, converting to dict and back should produce
    an equivalent object.
    
    **Validates: Requirements 10.6, 12.1, 12.2, 12.4**
    """
    # Convert to dict
    data_dict = market_data.to_dict()
    
    # Convert back to object
    restored = MarketData.from_dict(data_dict)
    
    # Should be equivalent
    assert restored.symbol == market_data.symbol
    assert restored.timestamp == market_data.timestamp
    assert restored.open == market_data.open
    assert restored.high == market_data.high
    assert restored.low == market_data.low
    assert restored.close == market_data.close
    assert restored.volume == market_data.volume


@given(
    symbol=st.text(min_size=1, max_size=10),
    timestamp=st.datetimes(min_value=datetime(2020, 1, 1)),
    action=st.sampled_from(["BUY", "SELL", "HOLD"]),
    confidence=st.floats(min_value=0.0, max_value=10.0),
    strategy=st.text(min_size=1, max_size=20),
    bullish_signals=st.lists(st.text(min_size=1, max_size=50), max_size=10),
    bearish_signals=st.lists(st.text(min_size=1, max_size=50), max_size=10)
)
def test_property_trading_signal_json_roundtrip(
    symbol, timestamp, action, confidence, strategy, bullish_signals, bearish_signals
):
    """
    **Property 23: Results Persistence Round-Trip (TradingSignal)**
    
    For any TradingSignal instance, converting to dict and back should produce
    an equivalent object.
    
    **Validates: Requirements 10.6, 12.1, 12.2, 12.4**
    """
    signal = TradingSignal(
        symbol=symbol,
        timestamp=timestamp,
        action=action,
        confidence=confidence,
        strategy=strategy,
        bullish_signals=bullish_signals,
        bearish_signals=bearish_signals
    )
    
    # Convert to dict
    signal_dict = signal.to_dict()
    
    # Convert back to object
    restored = TradingSignal.from_dict(signal_dict)
    
    # Should be equivalent
    assert restored.symbol == signal.symbol
    assert restored.timestamp == signal.timestamp
    assert restored.action == signal.action
    assert restored.confidence == signal.confidence
    assert restored.strategy == signal.strategy
    assert restored.bullish_signals == signal.bullish_signals
    assert restored.bearish_signals == signal.bearish_signals


@given(
    symbol=st.text(min_size=1, max_size=10),
    action=st.sampled_from(["BUY", "SELL"]),
    position_size=st.integers(min_value=1, max_value=10000),
    entry_price=st.floats(min_value=1.0, max_value=1000.0),
    stop_loss=st.floats(min_value=1.0, max_value=1000.0),
    take_profit=st.floats(min_value=1.0, max_value=1000.0),
    risk_amount=st.floats(min_value=0.0, max_value=100000.0),
    reward_amount=st.floats(min_value=0.0, max_value=100000.0),
    rr_ratio=st.floats(min_value=0.0, max_value=10.0)
)
def test_property_trade_plan_json_roundtrip(
    symbol, action, position_size, entry_price, stop_loss, take_profit,
    risk_amount, reward_amount, rr_ratio
):
    """
    **Property 23: Results Persistence Round-Trip (TradePlan)**
    
    For any TradePlan instance, converting to dict and back should produce
    an equivalent object.
    
    **Validates: Requirements 10.6, 12.1, 12.2, 12.4**
    """
    trade_plan = TradePlan(
        symbol=symbol,
        action=action,
        position_size=position_size,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_amount=risk_amount,
        reward_amount=reward_amount,
        rr_ratio=rr_ratio
    )
    
    # Convert to dict
    plan_dict = trade_plan.to_dict()
    
    # Convert back to object
    restored = TradePlan.from_dict(plan_dict)
    
    # Should be equivalent
    assert restored.symbol == trade_plan.symbol
    assert restored.action == trade_plan.action
    assert restored.position_size == trade_plan.position_size
    assert restored.entry_price == trade_plan.entry_price
    assert restored.stop_loss == trade_plan.stop_loss
    assert restored.take_profit == trade_plan.take_profit
    assert restored.risk_amount == trade_plan.risk_amount
    assert restored.reward_amount == trade_plan.reward_amount
    assert restored.rr_ratio == trade_plan.rr_ratio


@given(
    strategy=st.text(min_size=1, max_size=20),
    symbol=st.text(min_size=1, max_size=10),
    start_date=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2023, 12, 31)),
    end_date=st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31)),
    initial_capital=st.floats(min_value=1000.0, max_value=1_000_000.0),
    final_capital=st.floats(min_value=0.0, max_value=2_000_000.0),
    total_return=st.floats(min_value=-1.0, max_value=10.0),
    sharpe_ratio=st.floats(min_value=-5.0, max_value=5.0),
    max_drawdown=st.floats(min_value=0.0, max_value=1.0),
    win_rate=st.floats(min_value=0.0, max_value=1.0),
    profit_factor=st.floats(min_value=0.0, max_value=10.0),
    total_trades=st.integers(min_value=0, max_value=1000),
    winning_trades=st.integers(min_value=0, max_value=1000),
    losing_trades=st.integers(min_value=0, max_value=1000)
)
def test_property_backtest_result_json_roundtrip(
    strategy, symbol, start_date, end_date, initial_capital, final_capital,
    total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor,
    total_trades, winning_trades, losing_trades
):
    """
    **Property 23: Results Persistence Round-Trip (BacktestResult)**
    
    For any BacktestResult instance, converting to dict and back should produce
    an equivalent object.
    
    **Validates: Requirements 10.6, 12.1, 12.2, 12.4**
    """
    result = BacktestResult(
        strategy=strategy,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        final_capital=final_capital,
        total_return=total_return,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        profit_factor=profit_factor,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        trades=[],
        equity_curve=[]
    )
    
    # Convert to dict
    result_dict = result.to_dict()
    
    # Convert back to object
    restored = BacktestResult.from_dict(result_dict)
    
    # Should be equivalent
    assert restored.strategy == result.strategy
    assert restored.symbol == result.symbol
    assert restored.start_date == result.start_date
    assert restored.end_date == result.end_date
    assert restored.initial_capital == result.initial_capital
    assert restored.final_capital == result.final_capital
    assert restored.total_return == result.total_return
    assert restored.sharpe_ratio == result.sharpe_ratio
    assert restored.max_drawdown == result.max_drawdown
    assert restored.win_rate == result.win_rate
    assert restored.profit_factor == result.profit_factor
    assert restored.total_trades == result.total_trades
    assert restored.winning_trades == result.winning_trades
    assert restored.losing_trades == result.losing_trades


@given(
    mode=st.sampled_from(['analysis', 'paper', 'live']),
    portfolio_value=st.floats(min_value=100.0, max_value=1_000_000.0),
    max_risk_per_trade=st.floats(min_value=0.001, max_value=0.05),
    max_position_size=st.floats(min_value=0.01, max_value=1.0),
    max_portfolio_exposure=st.floats(min_value=0.1, max_value=1.0),
    strategy=st.text(min_size=1, max_size=20),
    symbols=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10),
    use_claude=st.booleans()
)
def test_property_trading_config_json_roundtrip(
    mode, portfolio_value, max_risk_per_trade, max_position_size,
    max_portfolio_exposure, strategy, symbols, use_claude
):
    """
    **Property 23: Results Persistence Round-Trip (TradingConfig)**
    
    For any TradingConfig instance, converting to dict and back should produce
    an equivalent object (excluding API keys for security).
    
    **Validates: Requirements 10.6, 12.1, 12.2, 12.4**
    """
    config = TradingConfig(
        mode=mode,
        portfolio_value=portfolio_value,
        max_risk_per_trade=max_risk_per_trade,
        max_position_size=max_position_size,
        max_portfolio_exposure=max_portfolio_exposure,
        strategy=strategy,
        symbols=symbols,
        use_claude=use_claude,
        anthropic_api_key="test_key",
        alpaca_api_key="test_alpaca_key",
        alpaca_secret_key="test_alpaca_secret"
    )
    
    # Convert to dict (API keys should be excluded)
    config_dict = config.to_dict()
    
    # API keys should not be in dict
    assert 'anthropic_api_key' not in config_dict
    assert 'alpaca_api_key' not in config_dict
    assert 'alpaca_secret_key' not in config_dict
    
    # Convert back to object (without API keys)
    restored = TradingConfig.from_dict(config_dict)
    
    # Should be equivalent (except API keys)
    assert restored.mode == config.mode
    assert restored.portfolio_value == config.portfolio_value
    assert restored.max_risk_per_trade == config.max_risk_per_trade
    assert restored.max_position_size == config.max_position_size
    assert restored.max_portfolio_exposure == config.max_portfolio_exposure
    assert restored.strategy == config.strategy
    assert restored.symbols == config.symbols
    assert restored.use_claude == config.use_claude
    # API keys should be None after restoration
    assert restored.anthropic_api_key is None
    assert restored.alpaca_api_key is None
    assert restored.alpaca_secret_key is None
