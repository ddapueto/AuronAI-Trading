"""Unit tests for configuration management.

**Validates: Requirements 9.1, 9.2, 9.4**
"""

import os
import tempfile
from pathlib import Path
import pytest

from auronai.core.models import TradingConfig


class TestTradingConfigLoading:
    """Test configuration loading from environment variables and .env files."""
    
    def test_from_env_with_defaults(self, monkeypatch):
        """Test loading configuration with all default values.
        
        **Validates: Requirements 9.1, 9.3**
        """
        # Clear any existing env vars
        for key in ['TRADING_MODE', 'PORTFOLIO_VALUE', 'MAX_RISK_PER_TRADE',
                    'MAX_POSITION_SIZE', 'MAX_PORTFOLIO_EXPOSURE', 'STRATEGY',
                    'SYMBOLS', 'USE_CLAUDE', 'ANTHROPIC_API_KEY',
                    'ALPACA_API_KEY', 'ALPACA_SECRET_KEY']:
            monkeypatch.delenv(key, raising=False)
        
        config = TradingConfig.from_env()
        
        # Verify defaults
        assert config.mode == 'analysis'
        assert config.portfolio_value == 10000.0
        assert config.max_risk_per_trade == 0.02
        assert config.max_position_size == 0.20
        assert config.max_portfolio_exposure == 0.80
        assert config.strategy == 'swing_weekly'
        assert config.symbols == ['AAPL', 'MSFT', 'NVDA']
        assert config.use_claude is True
        assert config.anthropic_api_key is None
        assert config.alpaca_api_key is None
        assert config.alpaca_secret_key is None
    
    def test_from_env_with_custom_values(self, monkeypatch):
        """Test loading configuration with custom environment variables.
        
        **Validates: Requirements 9.1, 9.2**
        """
        # Set custom env vars
        monkeypatch.setenv('TRADING_MODE', 'paper')
        monkeypatch.setenv('PORTFOLIO_VALUE', '50000.0')
        monkeypatch.setenv('MAX_RISK_PER_TRADE', '0.01')
        monkeypatch.setenv('MAX_POSITION_SIZE', '0.15')
        monkeypatch.setenv('MAX_PORTFOLIO_EXPOSURE', '0.70')
        monkeypatch.setenv('STRATEGY', 'day_trading')
        monkeypatch.setenv('SYMBOLS', 'TSLA,GOOGL,AMZN')
        monkeypatch.setenv('USE_CLAUDE', 'false')
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'test_anthropic_key')
        monkeypatch.setenv('ALPACA_API_KEY', 'test_alpaca_key')
        monkeypatch.setenv('ALPACA_SECRET_KEY', 'test_alpaca_secret')
        
        config = TradingConfig.from_env()
        
        # Verify custom values
        assert config.mode == 'paper'
        assert config.portfolio_value == 50000.0
        assert config.max_risk_per_trade == 0.01
        assert config.max_position_size == 0.15
        assert config.max_portfolio_exposure == 0.70
        assert config.strategy == 'day_trading'
        assert config.symbols == ['TSLA', 'GOOGL', 'AMZN']
        assert config.use_claude is False
        assert config.anthropic_api_key == 'test_anthropic_key'
        assert config.alpaca_api_key == 'test_alpaca_key'
        assert config.alpaca_secret_key == 'test_alpaca_secret'
    
    def test_from_env_with_dotenv_file(self, monkeypatch, tmp_path):
        """Test loading configuration from .env file.
        
        **Validates: Requirements 9.2**
        """
        # Simulate loading from .env by setting env vars
        # (In real usage, load_dotenv() would read these from .env file)
        monkeypatch.setenv('TRADING_MODE', 'live')
        monkeypatch.setenv('PORTFOLIO_VALUE', '100000.0')
        monkeypatch.setenv('MAX_RISK_PER_TRADE', '0.015')
        monkeypatch.setenv('MAX_POSITION_SIZE', '0.25')
        monkeypatch.setenv('MAX_PORTFOLIO_EXPOSURE', '0.85')
        monkeypatch.setenv('STRATEGY', 'swing_trading')
        monkeypatch.setenv('SYMBOLS', 'AAPL,MSFT,NVDA,GOOGL,TSLA')
        monkeypatch.setenv('USE_CLAUDE', 'true')
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-ant-test123')
        monkeypatch.setenv('ALPACA_API_KEY', 'PK-test456')
        monkeypatch.setenv('ALPACA_SECRET_KEY', 'SK-test789')
        
        config = TradingConfig.from_env()
        
        # Verify values (as if loaded from .env file)
        assert config.mode == 'live'
        assert config.portfolio_value == 100000.0
        assert config.max_risk_per_trade == 0.015
        assert config.max_position_size == 0.25
        assert config.max_portfolio_exposure == 0.85
        assert config.strategy == 'swing_trading'
        assert config.symbols == ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA']
        assert config.use_claude is True
        assert config.anthropic_api_key == 'sk-ant-test123'
        assert config.alpaca_api_key == 'PK-test456'
        assert config.alpaca_secret_key == 'SK-test789'


class TestTradingConfigValidation:
    """Test configuration validation."""
    
    def test_validate_valid_analysis_mode(self):
        """Test validation of valid analysis mode configuration.
        
        **Validates: Requirements 9.4**
        """
        config = TradingConfig(
            mode='analysis',
            portfolio_value=10000.0,
            max_risk_per_trade=0.02,
            max_position_size=0.20,
            max_portfolio_exposure=0.80,
            symbols=['AAPL', 'MSFT']
        )
        
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_invalid_mode(self):
        """Test validation detects invalid trading mode.
        
        **Validates: Requirements 9.4, 9.9**
        """
        config = TradingConfig(mode='invalid_mode')
        
        is_valid, errors = config.validate()
        assert not is_valid
        assert len(errors) > 0
        assert any('Invalid mode' in error for error in errors)
    
    def test_validate_invalid_risk_parameters(self):
        """Test validation detects invalid risk parameters.
        
        **Validates: Requirements 9.4, 9.9**
        """
        # Test max_risk_per_trade too high
        config = TradingConfig(max_risk_per_trade=0.10)  # 10% is too high
        is_valid, errors = config.validate()
        assert not is_valid
        assert any('max_risk_per_trade' in error for error in errors)
        
        # Test max_risk_per_trade negative
        config = TradingConfig(max_risk_per_trade=-0.01)
        is_valid, errors = config.validate()
        assert not is_valid
        assert any('max_risk_per_trade' in error for error in errors)
        
        # Test max_position_size too high
        config = TradingConfig(max_position_size=1.5)  # 150% is invalid
        is_valid, errors = config.validate()
        assert not is_valid
        assert any('max_position_size' in error for error in errors)
        
        # Test max_portfolio_exposure invalid
        config = TradingConfig(max_portfolio_exposure=0.0)
        is_valid, errors = config.validate()
        assert not is_valid
        assert any('max_portfolio_exposure' in error for error in errors)
    
    def test_validate_invalid_portfolio_value(self):
        """Test validation detects invalid portfolio value.
        
        **Validates: Requirements 9.4, 9.9**
        """
        config = TradingConfig(portfolio_value=-1000.0)
        
        is_valid, errors = config.validate()
        assert not is_valid
        assert any('portfolio_value' in error for error in errors)
    
    def test_validate_empty_symbols(self):
        """Test validation detects empty symbols list.
        
        **Validates: Requirements 9.4, 9.9**
        """
        config = TradingConfig(symbols=[])
        
        is_valid, errors = config.validate()
        assert not is_valid
        assert any('symbols' in error for error in errors)
    
    def test_validate_paper_mode_requires_api_keys(self):
        """Test validation requires Alpaca API keys for paper mode.
        
        **Validates: Requirements 9.4, 9.9**
        """
        config = TradingConfig(
            mode='paper',
            alpaca_api_key=None,
            alpaca_secret_key=None
        )
        
        is_valid, errors = config.validate()
        assert not is_valid
        assert any('Alpaca API keys required' in error for error in errors)
    
    def test_validate_live_mode_requires_api_keys(self):
        """Test validation requires Alpaca API keys for live mode.
        
        **Validates: Requirements 9.4, 9.9**
        """
        config = TradingConfig(
            mode='live',
            alpaca_api_key=None,
            alpaca_secret_key=None
        )
        
        is_valid, errors = config.validate()
        assert not is_valid
        assert any('Alpaca API keys required' in error for error in errors)
    
    def test_validate_paper_mode_with_api_keys(self):
        """Test validation passes for paper mode with API keys.
        
        **Validates: Requirements 9.4**
        """
        config = TradingConfig(
            mode='paper',
            alpaca_api_key='test_key',
            alpaca_secret_key='test_secret',
            symbols=['AAPL']
        )
        
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_multiple_errors(self):
        """Test validation returns all errors at once.
        
        **Validates: Requirements 9.4, 9.9**
        """
        config = TradingConfig(
            mode='invalid',
            portfolio_value=-100.0,
            max_risk_per_trade=0.10,
            symbols=[]
        )
        
        is_valid, errors = config.validate()
        assert not is_valid
        assert len(errors) >= 4  # Should have multiple errors
        assert any('mode' in error for error in errors)
        assert any('portfolio_value' in error for error in errors)
        assert any('max_risk_per_trade' in error for error in errors)
        assert any('symbols' in error for error in errors)


class TestTradingConfigSerialization:
    """Test configuration serialization."""
    
    def test_to_dict_excludes_api_keys(self):
        """Test that to_dict() excludes API keys for security.
        
        **Validates: Requirements 12.4**
        """
        config = TradingConfig(
            anthropic_api_key='secret_anthropic',
            alpaca_api_key='secret_alpaca',
            alpaca_secret_key='secret_alpaca_secret'
        )
        
        config_dict = config.to_dict()
        
        # API keys should not be in dict
        assert 'anthropic_api_key' not in config_dict
        assert 'alpaca_api_key' not in config_dict
        assert 'alpaca_secret_key' not in config_dict
        
        # Other fields should be present
        assert 'mode' in config_dict
        assert 'portfolio_value' in config_dict
        assert 'symbols' in config_dict
    
    def test_from_dict_restores_config(self):
        """Test that from_dict() restores configuration.
        
        **Validates: Requirements 12.4**
        """
        original = TradingConfig(
            mode='paper',
            portfolio_value=25000.0,
            symbols=['AAPL', 'GOOGL']
        )
        
        config_dict = original.to_dict()
        restored = TradingConfig.from_dict(config_dict)
        
        assert restored.mode == original.mode
        assert restored.portfolio_value == original.portfolio_value
        assert restored.symbols == original.symbols
        # API keys should be None after restoration
        assert restored.anthropic_api_key is None
        assert restored.alpaca_api_key is None
        assert restored.alpaca_secret_key is None
