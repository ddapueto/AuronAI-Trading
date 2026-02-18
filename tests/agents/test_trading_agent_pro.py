"""Unit tests for TradingAgentPro."""

import pytest
from unittest.mock import patch
import pandas as pd

from auronai.agents.trading_agent_pro import TradingAgentPro
from auronai.core.models import TradingConfig


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'Open': [100 + i * 0.5 for i in range(100)],
        'High': [101 + i * 0.5 for i in range(100)],
        'Low': [99 + i * 0.5 for i in range(100)],
        'Close': [100.5 + i * 0.5 for i in range(100)],
        'Volume': [1000000 + i * 10000 for i in range(100)]
    }, index=dates)
    return data


class TestTradingAgentProInitialization:
    """Test TradingAgentPro initialization."""
    
    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        agent = TradingAgentPro(mode="analysis")
        
        assert agent.mode == "analysis"
        assert agent.config is not None
        assert agent.indicators is not None
        # Verify advanced mode is enabled
        assert agent.indicators.advanced_mode is True
    
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = TradingConfig(
            portfolio_value=50000.0,
            max_risk_per_trade=0.01
        )
        agent = TradingAgentPro(mode="paper", config=config)
        
        assert agent.mode == "paper"
        assert agent.config.portfolio_value == 50000.0
        assert agent.indicators.advanced_mode is True
    
    def test_init_all_modes(self):
        """Test initialization with all valid modes."""
        for mode in ["analysis", "paper", "live"]:
            agent = TradingAgentPro(mode=mode)
            assert agent.mode == mode
            assert agent.indicators.advanced_mode is True
    
    def test_inherits_from_trading_agent(self):
        """Test that TradingAgentPro inherits from TradingAgent."""
        from auronai.agents.trading_agent import TradingAgent
        
        agent = TradingAgentPro(mode="analysis")
        assert isinstance(agent, TradingAgent)


class TestAdvancedIndicators:
    """Test that Pro version uses advanced indicators."""
    
    @patch('auronai.agents.trading_agent.TradingAgent._get_market_data')
    @patch('auronai.agents.trading_agent.SignalGenerator.generate_signal')
    @patch('auronai.agents.trading_agent.AIAnalyzer.analyze_market')
    def test_calculates_advanced_indicators(
        self,
        mock_ai_analyze,
        mock_generate_signal,
        mock_get_data,
        sample_ohlcv_data
    ):
        """
        Test that Pro version calculates all advanced indicators.
        
        **Validates: Requirements 1.5, 1.6, 1.7, 1.8**
        """
        # Setup mocks
        mock_get_data.return_value = sample_ohlcv_data
        mock_generate_signal.return_value = {
            'action': 'HOLD',
            'confidence': 5.0,
            'strategy': 'combo',
            'bullish_signals': [],
            'bearish_signals': []
        }
        mock_ai_analyze.return_value = {
            'action': 'HOLD',
            'confidence': 5.0,
            'bullish_signals': [],
            'bearish_signals': [],
            'reasoning': 'Test',
            'source': 'rule_based'
        }
        
        # Create Pro agent
        agent = TradingAgentPro(mode="analysis")
        
        # Run analysis
        result = agent.analyze_symbol('AAPL')
        
        # Verify analysis completed
        assert result['error'] is None
        assert 'indicators' in result
        
        indicators = result['indicators']
        
        # Verify basic indicators are present
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'ema_20' in indicators
        assert 'bollinger_bands' in indicators
        
        # Verify advanced indicators are present (Requirements 1.5, 1.6, 1.7, 1.8)
        assert 'stochastic' in indicators  # Requirement 1.5
        assert 'atr' in indicators  # Requirement 1.6
        assert 'obv' in indicators  # Requirement 1.7
        assert 'williams_r' in indicators  # Requirement 1.8
        assert 'cci' in indicators  # Requirement 1.8
        assert 'roc' in indicators  # Requirement 1.8
    
    @patch('auronai.agents.trading_agent.TradingAgent._get_market_data')
    @patch('auronai.agents.trading_agent.SignalGenerator.generate_signal')
    @patch('auronai.agents.trading_agent.AIAnalyzer.analyze_market')
    def test_advanced_indicators_in_output(
        self,
        mock_ai_analyze,
        mock_generate_signal,
        mock_get_data,
        sample_ohlcv_data
    ):
        """Test that advanced indicators appear in formatted output."""
        # Setup mocks
        mock_get_data.return_value = sample_ohlcv_data
        mock_generate_signal.return_value = {
            'action': 'HOLD',
            'confidence': 5.0,
            'strategy': 'combo',
            'bullish_signals': [],
            'bearish_signals': []
        }
        mock_ai_analyze.return_value = {
            'action': 'HOLD',
            'confidence': 5.0,
            'bullish_signals': [],
            'bearish_signals': [],
            'reasoning': 'Test',
            'source': 'rule_based'
        }
        
        # Create Pro agent
        agent = TradingAgentPro(mode="analysis")
        
        # Run analysis
        result = agent.analyze_symbol('AAPL')
        
        # Format output
        output = agent.format_analysis_output(result)
        
        # Verify advanced indicators appear in output
        # Stochastic should be mentioned
        assert 'Stochastic' in output or 'stochastic' in output.lower()
        
        # ATR should be mentioned
        assert 'ATR' in output


class TestProVersionWorkflow:
    """Test that Pro version uses same workflow as basic version."""
    
    @patch('auronai.agents.trading_agent.TradingAgent._get_market_data')
    @patch('auronai.agents.trading_agent.SignalGenerator.generate_signal')
    @patch('auronai.agents.trading_agent.AIAnalyzer.analyze_market')
    def test_same_workflow_as_basic(
        self,
        mock_ai_analyze,
        mock_generate_signal,
        mock_get_data,
        sample_ohlcv_data
    ):
        """Test that Pro version follows same workflow as basic version."""
        # Setup mocks
        mock_get_data.return_value = sample_ohlcv_data
        mock_generate_signal.return_value = {
            'action': 'BUY',
            'confidence': 8.5,
            'strategy': 'combo',
            'bullish_signals': ['Strong signal'],
            'bearish_signals': []
        }
        mock_ai_analyze.return_value = {
            'action': 'BUY',
            'confidence': 8.0,
            'bullish_signals': [],
            'bearish_signals': [],
            'reasoning': 'Test',
            'source': 'rule_based'
        }
        
        # Create Pro agent
        agent = TradingAgentPro(mode="analysis")
        
        # Run analysis
        result = agent.analyze_symbol('AAPL')
        
        # Verify workflow steps completed
        assert result['error'] is None
        assert 'current_price' in result
        assert 'indicators' in result
        assert 'signal' in result
        assert 'ai_analysis' in result
        assert 'trade_plan' in result
        
        # Verify trade plan was created for strong signal
        assert result['trade_plan'] is not None
        assert result['trade_plan']['action'] == 'BUY'
    
    def test_pro_version_has_all_basic_methods(self):
        """Test that Pro version has all methods from basic version."""
        agent = TradingAgentPro(mode="analysis")
        
        # Verify all key methods exist
        assert hasattr(agent, 'analyze_symbol')
        assert hasattr(agent, 'format_analysis_output')
        assert hasattr(agent, 'run_analysis')
        assert hasattr(agent, 'save_results')
        assert hasattr(agent, '_get_market_data')
        assert hasattr(agent, '_flatten_indicators')
        assert hasattr(agent, '_create_trade_plan')


class TestProVersionMultiSymbol:
    """Test Pro version with multiple symbols."""
    
    @patch('auronai.agents.trading_agent.TradingAgent._get_market_data')
    @patch('auronai.agents.trading_agent.SignalGenerator.generate_signal')
    @patch('auronai.agents.trading_agent.AIAnalyzer.analyze_market')
    def test_run_analysis_multiple_symbols(
        self,
        mock_ai_analyze,
        mock_generate_signal,
        mock_get_data,
        sample_ohlcv_data
    ):
        """Test running analysis for multiple symbols with Pro version."""
        # Setup mocks
        mock_get_data.return_value = sample_ohlcv_data
        mock_generate_signal.return_value = {
            'action': 'HOLD',
            'confidence': 5.0,
            'strategy': 'combo',
            'bullish_signals': [],
            'bearish_signals': []
        }
        mock_ai_analyze.return_value = {
            'action': 'HOLD',
            'confidence': 5.0,
            'bullish_signals': [],
            'bearish_signals': [],
            'reasoning': 'Test',
            'source': 'rule_based'
        }
        
        # Create Pro agent
        agent = TradingAgentPro(mode="analysis")
        
        # Run analysis for multiple symbols
        symbols = ['AAPL', 'MSFT', 'NVDA']
        results = agent.run_analysis(symbols)
        
        # Verify results
        assert len(results) == 3
        
        # Verify each result has advanced indicators
        for result in results:
            assert result['error'] is None
            assert 'stochastic' in result['indicators']
            assert 'atr' in result['indicators']
            assert 'obv' in result['indicators']
