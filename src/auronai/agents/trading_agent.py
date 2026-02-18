"""Trading agent orchestrating complete trading workflow."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import os

from auronai.core.models import TradingConfig, TradingSignal, TradePlan
from auronai.data.market_data_provider import MarketDataProvider
from auronai.data.demo_simulator import DemoSimulator
from auronai.indicators.technical_indicators import TechnicalIndicators
from auronai.analysis.signal_generator import SignalGenerator
from auronai.analysis.ai_analyzer import AIAnalyzer
from auronai.risk.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class TradingAgent:
    """
    Trading agent that orchestrates the complete trading workflow.
    
    Integrates data retrieval, technical analysis, signal generation,
    AI analysis, and risk management to produce actionable trade recommendations.
    """
    
    def __init__(
        self,
        mode: str = "analysis",
        config: Optional[TradingConfig] = None
    ):
        """
        Initialize trading agent.
        
        Args:
            mode: Trading mode - "analysis", "paper", or "live"
            config: Trading configuration (uses defaults if None)
            
        Raises:
            ValueError: If mode is invalid
        """
        if mode not in ["analysis", "paper", "live"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'analysis', 'paper', or 'live'")
        
        self.mode = mode
        self.config = config or TradingConfig()
        
        # Initialize components
        self.market_data = MarketDataProvider()
        self.demo_simulator = DemoSimulator()
        self.indicators = TechnicalIndicators(advanced_mode=False)
        self.signal_generator = SignalGenerator()
        self.ai_analyzer = AIAnalyzer(api_key=self.config.anthropic_api_key)
        self.risk_manager = RiskManager(
            portfolio_value=self.config.portfolio_value,
            max_risk_per_trade=self.config.max_risk_per_trade,
            max_position_size=self.config.max_position_size,
            max_portfolio_exposure=self.config.max_portfolio_exposure
        )
        
        logger.info(f"TradingAgent initialized in {mode} mode")
    
    def analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Perform complete analysis for a symbol.
        
        Workflow:
        1. Retrieve market data (or generate simulated data)
        2. Calculate technical indicators
        3. Generate trading signals
        4. Get AI analysis (if available)
        5. Calculate risk parameters
        6. Create trade plan
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Dictionary with complete analysis:
            {
                'symbol': str,
                'timestamp': datetime,
                'current_price': float,
                'indicators': Dict[str, Any],
                'signal': Dict[str, Any],
                'ai_analysis': Dict[str, Any],
                'trade_plan': Dict[str, Any] or None,
                'mode': str,
                'error': str or None
            }
        """
        logger.info(f"Analyzing {symbol} in {self.mode} mode")
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'mode': self.mode,
            'error': None
        }
        
        try:
            # Step 1: Retrieve market data
            data = self._get_market_data(symbol)
            if data is None or data.empty:
                result['error'] = f"Failed to retrieve data for {symbol}"
                logger.error(result['error'])
                return result
            
            current_price = float(data['Close'].iloc[-1])
            result['current_price'] = current_price
            
            # Step 2: Calculate technical indicators
            indicators_dict = self.indicators.calculate_all_indicators(data)
            if not indicators_dict:
                result['error'] = "Failed to calculate indicators"
                logger.error(result['error'])
                return result
            
            # Flatten indicators for easier access
            flat_indicators = self._flatten_indicators(indicators_dict, current_price)
            result['indicators'] = indicators_dict
            
            # Step 3: Generate trading signal
            signal = self.signal_generator.generate_signal(
                flat_indicators,
                strategy=self.config.strategy
            )
            result['signal'] = signal
            
            # Step 4: Get AI analysis
            ai_analysis = self.ai_analyzer.analyze_market(
                symbol=symbol,
                indicators=flat_indicators,
                current_price=current_price
            )
            result['ai_analysis'] = ai_analysis
            
            # Step 5: Calculate risk parameters and create trade plan
            if signal['action'] in ['BUY', 'SELL'] and signal['confidence'] >= 7.0:
                trade_plan = self._create_trade_plan(
                    symbol=symbol,
                    action=signal['action'],
                    entry_price=current_price,
                    indicators=flat_indicators,
                    confidence=signal['confidence']
                )
                result['trade_plan'] = trade_plan
            else:
                result['trade_plan'] = None
                logger.info(f"No actionable signal for {symbol}: {signal['action']} with confidence {signal['confidence']}")
            
            logger.info(f"Analysis complete for {symbol}: {signal['action']} (confidence: {signal['confidence']})")
            
        except Exception as e:
            result['error'] = f"Analysis failed: {str(e)}"
            logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
        
        return result
    
    def _get_market_data(self, symbol: str):
        """
        Retrieve market data with fallback to demo mode.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # Try real data first
            data = self.market_data.get_historical_data(
                symbol,
                period='3mo',  # 3 months for sufficient indicator calculation
                interval='1d'
            )
            
            if data is not None and not data.empty:
                logger.debug(f"Retrieved {len(data)} rows of real data for {symbol}")
                return data
            
        except Exception as e:
            logger.warning(f"Failed to retrieve real data for {symbol}: {e}")
        
        # Fallback to demo data
        logger.info(f"Using demo data for {symbol}")
        return self.demo_simulator.generate_price_data(
            symbol=symbol,
            days=90,
            volatility=0.02
        )
    
    def _flatten_indicators(
        self,
        indicators_dict: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        Flatten nested indicator dictionary for easier access.
        
        Args:
            indicators_dict: Nested indicator dictionary
            current_price: Current price
            
        Returns:
            Flattened dictionary with all indicator values
        """
        flat = {'close': current_price}
        
        for key, value in indicators_dict.items():
            if isinstance(value, dict):
                # Extract 'value' field if present
                if 'value' in value:
                    flat[key] = value['value']
                # Extract specific fields for complex indicators
                if key == 'macd':
                    flat['macd'] = value.get('value')
                    flat['macd_signal'] = value.get('signal')
                    flat['macd_histogram'] = value.get('histogram')
                elif key == 'bollinger_bands':
                    flat['bb_upper'] = value.get('upper')
                    flat['bb_middle'] = value.get('middle')
                    flat['bb_lower'] = value.get('lower')
                elif key == 'stochastic':
                    flat['stochastic_k'] = value.get('k')
                    flat['stochastic_d'] = value.get('d')
            else:
                flat[key] = value
        
        # Add previous values for trend detection
        if 'rsi' in indicators_dict and 'previous' in indicators_dict['rsi']:
            flat['rsi_prev'] = indicators_dict['rsi']['previous']
        if 'macd' in indicators_dict:
            flat['macd_prev'] = indicators_dict['macd'].get('value')
            flat['macd_signal_prev'] = indicators_dict['macd'].get('signal')
        
        return flat
    
    def _create_trade_plan(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        indicators: Dict[str, Any],
        confidence: float
    ) -> Optional[Dict[str, Any]]:
        """
        Create complete trade plan with risk management.
        
        Args:
            symbol: Stock symbol
            action: Trade action (BUY or SELL)
            entry_price: Entry price
            indicators: Flattened indicators dictionary
            confidence: Signal confidence (0-10)
            
        Returns:
            Trade plan dictionary or None if plan cannot be created
        """
        try:
            # Calculate stop loss using ATR
            atr = indicators.get('atr')
            if atr is None:
                logger.warning(f"ATR not available for {symbol}, using 2% stop")
                atr = entry_price * 0.02
            
            direction = "long" if action == "BUY" else "short"
            stop_loss = self.risk_manager.calculate_stop_loss(
                entry_price=entry_price,
                atr=atr,
                direction=direction
            )
            
            if stop_loss is None:
                logger.error(f"Failed to calculate stop loss for {symbol}")
                return None
            
            # Calculate position size using Kelly Criterion
            # Use confidence as proxy for win probability (confidence/10)
            win_probability = min(confidence / 10.0, 0.9)  # Cap at 90%
            
            # For short positions, we need to adjust the calculation
            # The risk manager expects stop_loss < entry_price for longs
            # For shorts, we pass the values as if it were a long to get correct sizing
            if action == "SELL":
                # For shorts: risk = stop_loss - entry_price
                # We calculate as if it were a long with inverted prices
                position_size = self.risk_manager.calculate_position_size(
                    entry_price=stop_loss,  # Swap for calculation
                    stop_loss=entry_price,  # Swap for calculation
                    win_probability=win_probability,
                    rr_ratio=2.0
                )
            else:
                position_size = self.risk_manager.calculate_position_size(
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    win_probability=win_probability,
                    rr_ratio=2.0
                )
            
            if position_size == 0:
                logger.warning(f"Position size is 0 for {symbol}, insufficient capital or invalid parameters")
                return None
            
            # Calculate take profit
            take_profit = self.risk_manager.calculate_take_profit(
                entry_price=entry_price,
                stop_loss=stop_loss,
                rr_ratio=2.0
            )
            
            if take_profit is None:
                logger.error(f"Failed to calculate take profit for {symbol}")
                return None
            
            # Calculate risk and reward amounts
            risk_per_share = abs(entry_price - stop_loss)
            reward_per_share = abs(take_profit - entry_price)
            
            risk_amount = position_size * risk_per_share
            reward_amount = position_size * reward_per_share
            rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # Validate trade
            is_valid, message = self.risk_manager.validate_trade(
                position_size=position_size,
                entry_price=entry_price,
                current_exposure=0.0  # TODO: Track actual portfolio exposure
            )
            
            if not is_valid:
                logger.warning(f"Trade validation failed for {symbol}: {message}")
                return None
            
            trade_plan = {
                'symbol': symbol,
                'action': action,
                'position_size': position_size,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_amount': risk_amount,
                'reward_amount': reward_amount,
                'rr_ratio': rr_ratio,
                'validation': message
            }
            
            logger.info(
                f"Trade plan created for {symbol}: {action} {position_size} shares @ ${entry_price:.2f}, "
                f"SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}, R/R: {rr_ratio:.2f}"
            )
            
            return trade_plan
            
        except Exception as e:
            logger.error(f"Error creating trade plan for {symbol}: {e}", exc_info=True)
            return None

    def format_analysis_output(self, result: Dict[str, Any]) -> str:
        """
        Format analysis result as user-friendly Spanish output with emojis.
        
        Args:
            result: Analysis result dictionary from analyze_symbol()
            
        Returns:
            Formatted string with sections for display
            
        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.7, 10.8, 7.10**
        """
        lines = []
        
        # Header with mode indicator
        mode_emoji = {
            'analysis': '📊',
            'paper': '📝',
            'live': '🔴'
        }
        mode_text = {
            'analysis': 'ANÁLISIS',
            'paper': 'PAPER TRADING',
            'live': 'TRADING EN VIVO'
        }
        
        lines.append("=" * 70)
        lines.append(f"{mode_emoji.get(result['mode'], '📊')} MODO: {mode_text.get(result['mode'], 'ANÁLISIS')}")
        lines.append(f"🎯 SÍMBOLO: {result['symbol']}")
        lines.append(f"🕐 FECHA: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if result.get('error'):
            lines.append("=" * 70)
            lines.append(f"❌ ERROR: {result['error']}")
            lines.append("=" * 70)
            return "\n".join(lines)
        
        lines.append(f"💰 PRECIO ACTUAL: ${result['current_price']:.2f}")
        lines.append("=" * 70)
        
        # Section 1: Technical Indicators
        lines.append("\n📈 INDICADORES TÉCNICOS")
        lines.append("-" * 70)
        
        indicators = result.get('indicators', {})
        
        # RSI
        if 'rsi' in indicators:
            rsi_val = indicators['rsi']['value']
            rsi_trend = "↑" if indicators['rsi']['trend'] == 'up' else "↓"
            rsi_color = "🟢" if rsi_val < 30 else "🔴" if rsi_val > 70 else "🟡"
            lines.append(f"  {rsi_color} RSI(14): {rsi_val:.2f} {rsi_trend}")
        
        # MACD
        if 'macd' in indicators:
            macd = indicators['macd']
            macd_trend = "🟢" if macd['trend'] == 'bullish' else "🔴"
            lines.append(f"  {macd_trend} MACD: {macd['value']:.4f} | Señal: {macd['signal']:.4f}")
        
        # EMAs
        for period in [20, 50, 200]:
            key = f'ema_{period}'
            if key in indicators:
                ema = indicators[key]
                trend = "↑" if ema['trend'] == 'up' else "↓"
                lines.append(f"  📊 EMA{period}: ${ema['value']:.2f} {trend}")
        
        # Bollinger Bands
        if 'bollinger_bands' in indicators:
            bb = indicators['bollinger_bands']
            position_emoji = {
                'above_upper': '🔴',
                'upper_half': '🟡',
                'lower_half': '🟡',
                'below_lower': '🟢'
            }
            emoji = position_emoji.get(bb['position'], '⚪')
            lines.append(f"  {emoji} Bollinger: Superior ${bb['upper']:.2f} | Medio ${bb['middle']:.2f} | Inferior ${bb['lower']:.2f}")
        
        # Advanced indicators (if present)
        if 'stochastic' in indicators:
            stoch = indicators['stochastic']
            stoch_emoji = "🟢" if stoch['k'] < 20 else "🔴" if stoch['k'] > 80 else "🟡"
            lines.append(f"  {stoch_emoji} Stochastic: %K {stoch['k']:.2f} | %D {stoch['d']:.2f}")
        
        if 'atr' in indicators:
            atr = indicators['atr']
            lines.append(f"  📏 ATR(14): ${atr['value']:.4f}")
        
        # Section 2: Trading Signal
        lines.append("\n🎯 SEÑAL DE TRADING")
        lines.append("-" * 70)
        
        signal = result.get('signal', {})
        action = signal.get('action', 'HOLD')
        confidence = signal.get('confidence', 0)
        
        action_emoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }
        action_text = {
            'BUY': 'COMPRAR',
            'SELL': 'VENDER',
            'HOLD': 'MANTENER'
        }
        
        lines.append(f"  {action_emoji.get(action, '⚪')} ACCIÓN: {action_text.get(action, action)}")
        
        # Confidence bar
        confidence_bars = int(confidence)
        confidence_display = "█" * confidence_bars + "░" * (10 - confidence_bars)
        lines.append(f"  💪 CONFIANZA: {confidence:.1f}/10 [{confidence_display}]")
        lines.append(f"  📋 ESTRATEGIA: {signal.get('strategy', 'N/A').upper()}")
        
        # Section 3: Bullish/Bearish Signals
        lines.append("\n📊 ANÁLISIS DE SEÑALES")
        lines.append("-" * 70)
        
        bullish = signal.get('bullish_signals', [])
        bearish = signal.get('bearish_signals', [])
        
        if bullish:
            lines.append("  🟢 SEÑALES ALCISTAS:")
            for sig in bullish:
                lines.append(f"    • {sig}")
        else:
            lines.append("  🟢 SEÑALES ALCISTAS: Ninguna")
        
        lines.append("")
        
        if bearish:
            lines.append("  🔴 SEÑALES BAJISTAS:")
            for sig in bearish:
                lines.append(f"    • {sig}")
        else:
            lines.append("  🔴 SEÑALES BAJISTAS: Ninguna")
        
        # Section 4: AI Analysis
        ai_analysis = result.get('ai_analysis', {})
        if ai_analysis:
            lines.append("\n🤖 ANÁLISIS AI")
            lines.append("-" * 70)
            
            ai_action = ai_analysis.get('action', 'HOLD')
            ai_confidence = ai_analysis.get('confidence', 0)
            source = ai_analysis.get('source', 'unknown')
            
            source_text = "Claude API" if source == "claude_api" else "Reglas Técnicas"
            lines.append(f"  🔍 FUENTE: {source_text}")
            lines.append(f"  {action_emoji.get(ai_action, '⚪')} RECOMENDACIÓN: {action_text.get(ai_action, ai_action)}")
            lines.append(f"  💪 CONFIANZA: {ai_confidence:.1f}/10")
            
            if ai_analysis.get('reasoning'):
                lines.append(f"  💭 RAZONAMIENTO: {ai_analysis['reasoning']}")
        
        # Section 5: Trade Plan
        trade_plan = result.get('trade_plan')
        if trade_plan:
            lines.append("\n💼 PLAN DE TRADING")
            lines.append("-" * 70)
            
            lines.append(f"  {action_emoji.get(trade_plan['action'], '⚪')} ACCIÓN: {action_text.get(trade_plan['action'], trade_plan['action'])}")
            lines.append(f"  📦 TAMAÑO POSICIÓN: {trade_plan['position_size']} acciones")
            lines.append(f"  💵 PRECIO ENTRADA: ${trade_plan['entry_price']:.2f}")
            lines.append(f"  🛑 STOP LOSS: ${trade_plan['stop_loss']:.2f}")
            lines.append(f"  🎯 TAKE PROFIT: ${trade_plan['take_profit']:.2f}")
            lines.append(f"  ⚠️  RIESGO: ${trade_plan['risk_amount']:.2f}")
            lines.append(f"  💰 RECOMPENSA: ${trade_plan['reward_amount']:.2f}")
            lines.append(f"  📊 RATIO R/R: {trade_plan['rr_ratio']:.2f}:1")
            
            # Calculate total position value
            position_value = trade_plan['position_size'] * trade_plan['entry_price']
            lines.append(f"  💼 VALOR TOTAL: ${position_value:.2f}")
        else:
            lines.append("\n💼 PLAN DE TRADING")
            lines.append("-" * 70)
            lines.append("  ℹ️  No se generó plan de trading (señal débil o HOLD)")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def run_analysis(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Run analysis for multiple symbols.
        
        Args:
            symbols: List of stock symbols to analyze
            
        Returns:
            List of analysis results, one per symbol
            
        **Validates: Requirements 2.3**
        """
        logger.info(f"Running analysis for {len(symbols)} symbols")
        
        results = []
        for symbol in symbols:
            logger.info(f"Analyzing {symbol}...")
            result = self.analyze_symbol(symbol)
            results.append(result)
            
            # Print formatted output
            print(self.format_analysis_output(result))
            print()  # Extra line between symbols
        
        logger.info(f"Analysis complete for {len(results)} symbols")
        return results
    
    def save_results(
        self,
        results: List[Dict[str, Any]],
        filename: str = "trading_results.json"
    ) -> bool:
        """
        Save analysis results to JSON file.
        
        Creates a backup of existing file before overwriting.
        
        Args:
            results: List of analysis results
            filename: Output filename (default: trading_results.json)
            
        Returns:
            True if save successful, False otherwise
            
        **Validates: Requirements 10.6, 12.1, 12.5**
        """
        try:
            # Create backup if file exists
            if os.path.exists(filename):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f"{filename}.{timestamp}.backup"
                try:
                    import shutil
                    shutil.copy2(filename, backup_filename)
                    logger.info(f"Created backup: {backup_filename}")
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
                    # Continue anyway - backup failure shouldn't prevent save
            
            # Prepare results for JSON serialization
            serializable_results = []
            for result in results:
                serializable = result.copy()
                # Convert datetime to ISO format
                if 'timestamp' in serializable:
                    serializable['timestamp'] = serializable['timestamp'].isoformat()
                serializable_results.append(serializable)
            
            # Add metadata
            output = {
                'metadata': {
                    'version': '0.1.0',
                    'generated_at': datetime.now().isoformat(),
                    'mode': self.mode,
                    'config': self.config.to_dict()
                },
                'results': serializable_results
            }
            
            # Write to file with pretty formatting
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save results to {filename}: {e}", exc_info=True)
            return False
