"""Technical indicator calculator using pandas-ta.

This module provides calculation of technical indicators for market analysis.
Supports both basic indicators (RSI, MACD, Bollinger Bands, EMA) and advanced
indicators (Stochastic, ATR, OBV, Williams %R, CCI, ROC).
"""

from typing import Dict, Any, Optional
import pandas as pd
import pandas_ta as ta

from auronai.utils.logger import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators from OHLCV data."""
    
    def __init__(self, advanced_mode: bool = False):
        """Initialize technical indicators calculator.
        
        Args:
            advanced_mode: If True, calculate all 15+ indicators (Pro version)
                          If False, calculate only basic indicators
        """
        self.advanced_mode = advanced_mode
        logger.info(f"TechnicalIndicators initialized (advanced_mode={advanced_mode})")
    
    def calculate_rsi(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> Optional[pd.Series]:
        """Calculate Relative Strength Index.
        
        Args:
            data: DataFrame with 'Close' column
            period: RSI period (default: 14)
            
        Returns:
            Series with RSI values (0-100) or None if insufficient data
            
        **Validates: Requirements 1.1**
        """
        if len(data) < period:
            logger.warning(f"Insufficient data for RSI: {len(data)} < {period}")
            return None
        
        try:
            rsi = ta.rsi(data['Close'], length=period)
            
            # Clip RSI values to 0-100 range (pandas-ta sometimes returns values slightly outside)
            if rsi is not None:
                rsi = rsi.clip(lower=0, upper=100)
            
            logger.debug(f"RSI calculated: latest={rsi.iloc[-1]:.2f}")
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return None
    
    def calculate_macd(
        self,
        data: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Optional[Dict[str, pd.Series]]:
        """Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            data: DataFrame with 'Close' column
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            
        Returns:
            Dictionary with 'macd', 'signal', 'histogram' Series
            Returns None if insufficient data
            
        **Validates: Requirements 1.2**
        """
        min_periods = slow + signal
        if len(data) < min_periods:
            logger.warning(f"Insufficient data for MACD: {len(data)} < {min_periods}")
            return None
        
        try:
            macd_result = ta.macd(data['Close'], fast=fast, slow=slow, signal=signal)
            
            if macd_result is None or macd_result.empty:
                logger.warning("MACD calculation returned empty result")
                return None
            
            result = {
                'macd': macd_result[f'MACD_{fast}_{slow}_{signal}'],
                'signal': macd_result[f'MACDs_{fast}_{slow}_{signal}'],
                'histogram': macd_result[f'MACDh_{fast}_{slow}_{signal}']
            }
            
            logger.debug(
                f"MACD calculated: macd={result['macd'].iloc[-1]:.4f}, "
                f"signal={result['signal'].iloc[-1]:.4f}"
            )
            return result
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return None
    
    def calculate_bollinger_bands(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std: float = 2.0
    ) -> Optional[Dict[str, pd.Series]]:
        """Calculate Bollinger Bands.
        
        Args:
            data: DataFrame with 'Close' column
            period: Moving average period (default: 20)
            std: Standard deviation multiplier (default: 2.0)
            
        Returns:
            Dictionary with 'upper', 'middle', 'lower' Series
            Returns None if insufficient data
            
        **Validates: Requirements 1.3**
        """
        if len(data) < period:
            logger.warning(f"Insufficient data for Bollinger Bands: {len(data)} < {period}")
            return None
        
        try:
            bb_result = ta.bbands(data['Close'], length=period, std=std)
            
            if bb_result is None or bb_result.empty:
                logger.warning("Bollinger Bands calculation returned empty result")
                return None
            
            # pandas-ta returns columns with format: BBL_length_std, BBM_length_std, BBU_length_std
            # Find the actual column names
            bb_cols = [col for col in bb_result.columns if 'BB' in col]
            
            if len(bb_cols) < 3:
                logger.error(f"Bollinger Bands missing columns. Found: {bb_cols}")
                return None
            
            # Sort to get lower, middle, upper
            lower_col = [col for col in bb_cols if col.startswith('BBL')][0]
            middle_col = [col for col in bb_cols if col.startswith('BBM')][0]
            upper_col = [col for col in bb_cols if col.startswith('BBU')][0]
            
            result = {
                'upper': bb_result[upper_col],
                'middle': bb_result[middle_col],
                'lower': bb_result[lower_col]
            }
            
            logger.debug(
                f"Bollinger Bands calculated: "
                f"upper={result['upper'].iloc[-1]:.2f}, "
                f"middle={result['middle'].iloc[-1]:.2f}, "
                f"lower={result['lower'].iloc[-1]:.2f}"
            )
            return result
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return None
    
    def calculate_ema(
        self,
        data: pd.DataFrame,
        period: int
    ) -> Optional[pd.Series]:
        """Calculate Exponential Moving Average.
        
        Args:
            data: DataFrame with 'Close' column
            period: EMA period (e.g., 20, 50, 200)
            
        Returns:
            Series with EMA values or None if insufficient data
            
        **Validates: Requirements 1.4**
        """
        if len(data) < period:
            logger.warning(f"Insufficient data for EMA{period}: {len(data)} < {period}")
            return None
        
        try:
            ema = ta.ema(data['Close'], length=period)
            logger.debug(f"EMA{period} calculated: latest={ema.iloc[-1]:.2f}")
            return ema
        except Exception as e:
            logger.error(f"Error calculating EMA{period}: {e}")
            return None
    
    def calculate_stochastic(
        self,
        data: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3
    ) -> Optional[Dict[str, pd.Series]]:
        """Calculate Stochastic Oscillator.
        
        Args:
            data: DataFrame with 'High', 'Low', 'Close' columns
            k_period: %K period (default: 14)
            d_period: %D smoothing period (default: 3)
            
        Returns:
            Dictionary with 'k' and 'd' Series (0-100)
            Returns None if insufficient data
            
        **Validates: Requirements 1.5**
        """
        min_periods = k_period + d_period
        if len(data) < min_periods:
            logger.warning(f"Insufficient data for Stochastic: {len(data)} < {min_periods}")
            return None
        
        try:
            stoch_result = ta.stoch(
                data['High'],
                data['Low'],
                data['Close'],
                k=k_period,
                d=d_period
            )
            
            if stoch_result is None or stoch_result.empty:
                logger.warning("Stochastic calculation returned empty result")
                return None
            
            result = {
                'k': stoch_result[f'STOCHk_{k_period}_{d_period}_3'],
                'd': stoch_result[f'STOCHd_{k_period}_{d_period}_3']
            }
            
            logger.debug(
                f"Stochastic calculated: k={result['k'].iloc[-1]:.2f}, "
                f"d={result['d'].iloc[-1]:.2f}"
            )
            return result
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {e}")
            return None
    
    def calculate_atr(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> Optional[pd.Series]:
        """Calculate Average True Range.
        
        Args:
            data: DataFrame with 'High', 'Low', 'Close' columns
            period: ATR period (default: 14)
            
        Returns:
            Series with ATR values or None if insufficient data
            
        **Validates: Requirements 1.6**
        """
        if len(data) < period + 1:
            logger.warning(f"Insufficient data for ATR: {len(data)} < {period + 1}")
            return None
        
        try:
            atr = ta.atr(data['High'], data['Low'], data['Close'], length=period)
            logger.debug(f"ATR calculated: latest={atr.iloc[-1]:.4f}")
            return atr
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return None
    
    def calculate_obv(self, data: pd.DataFrame) -> Optional[pd.Series]:
        """Calculate On-Balance Volume.
        
        Args:
            data: DataFrame with 'Close' and 'Volume' columns
            
        Returns:
            Series with OBV values or None if insufficient data
            
        **Validates: Requirements 1.7**
        """
        if len(data) < 2:
            logger.warning(f"Insufficient data for OBV: {len(data)} < 2")
            return None
        
        try:
            obv = ta.obv(data['Close'], data['Volume'])
            logger.debug(f"OBV calculated: latest={obv.iloc[-1]:.0f}")
            return obv
        except Exception as e:
            logger.error(f"Error calculating OBV: {e}")
            return None

    def calculate_williams_r(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> Optional[pd.Series]:
        """Calculate Williams %R.
        
        Args:
            data: DataFrame with 'High', 'Low', 'Close' columns
            period: Lookback period (default: 14)
            
        Returns:
            Series with Williams %R values (-100 to 0) or None if insufficient data
            
        **Validates: Requirements 1.8**
        """
        if len(data) < period:
            logger.warning(f"Insufficient data for Williams %R: {len(data)} < {period}")
            return None
        
        try:
            willr = ta.willr(data['High'], data['Low'], data['Close'], length=period)
            logger.debug(f"Williams %R calculated: latest={willr.iloc[-1]:.2f}")
            return willr
        except Exception as e:
            logger.error(f"Error calculating Williams %R: {e}")
            return None
    
    def calculate_cci(
        self,
        data: pd.DataFrame,
        period: int = 20
    ) -> Optional[pd.Series]:
        """Calculate Commodity Channel Index.
        
        Args:
            data: DataFrame with 'High', 'Low', 'Close' columns
            period: CCI period (default: 20)
            
        Returns:
            Series with CCI values or None if insufficient data
            
        **Validates: Requirements 1.8**
        """
        if len(data) < period:
            logger.warning(f"Insufficient data for CCI: {len(data)} < {period}")
            return None
        
        try:
            cci = ta.cci(data['High'], data['Low'], data['Close'], length=period)
            logger.debug(f"CCI calculated: latest={cci.iloc[-1]:.2f}")
            return cci
        except Exception as e:
            logger.error(f"Error calculating CCI: {e}")
            return None
    
    def calculate_roc(
        self,
        data: pd.DataFrame,
        period: int = 12
    ) -> Optional[pd.Series]:
        """Calculate Rate of Change.
        
        Args:
            data: DataFrame with 'Close' column
            period: ROC period (default: 12)
            
        Returns:
            Series with ROC values (percentage) or None if insufficient data
            
        **Validates: Requirements 1.8**
        """
        if len(data) < period + 1:
            logger.warning(f"Insufficient data for ROC: {len(data)} < {period + 1}")
            return None
        
        try:
            roc = ta.roc(data['Close'], length=period)
            logger.debug(f"ROC calculated: latest={roc.iloc[-1]:.2f}")
            return roc
        except Exception as e:
            logger.error(f"Error calculating ROC: {e}")
            return None
    
    def calculate_adx(
        self,
        data: pd.DataFrame,
        period: int = 14
    ) -> Optional[pd.Series]:
        """Calculate Average Directional Index (ADX).
        
        ADX measures trend strength regardless of direction.
        Values above 25 indicate strong trend, below 20 indicate weak trend.
        
        Args:
            data: DataFrame with 'High', 'Low', 'Close' columns
            period: ADX period (default: 14)
            
        Returns:
            Series with ADX values (0-100) or None if insufficient data
            
        **Validates: Requirements 1.8**
        """
        if len(data) < period * 2:
            logger.warning(f"Insufficient data for ADX: {len(data)} < {period * 2}")
            return None
        
        try:
            adx_result = ta.adx(
                data['High'],
                data['Low'],
                data['Close'],
                length=period
            )
            
            if adx_result is None or adx_result.empty:
                logger.warning("ADX calculation returned empty result")
                return None
            
            # pandas-ta returns DataFrame with ADX_period, DMP_period, DMN_period
            # We only need the ADX column
            adx_col = [col for col in adx_result.columns if col.startswith('ADX')][0]
            adx = adx_result[adx_col]
            
            logger.debug(f"ADX calculated: latest={adx.iloc[-1]:.2f}")
            return adx
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            return None
    
    def calculate_all_indicators(
        self,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate all indicators and return standardized format.
        
        Args:
            data: DataFrame with OHLCV columns
            
        Returns:
            Dictionary with all indicator values in standardized format:
            {
                'rsi': {'value': float, 'previous': float, 'trend': str},
                'macd': {'value': float, 'signal': float, 'histogram': float, 'trend': str},
                ...
            }
            
        **Validates: Requirements 1.9, 1.10**
        """
        logger.info(f"Calculating all indicators (advanced_mode={self.advanced_mode})")
        
        result = {}
        
        # Basic indicators (always calculated)
        
        # RSI
        rsi = self.calculate_rsi(data)
        if rsi is not None and len(rsi) >= 2:
            result['rsi'] = {
                'value': float(rsi.iloc[-1]),
                'previous': float(rsi.iloc[-2]),
                'trend': 'up' if rsi.iloc[-1] > rsi.iloc[-2] else 'down'
            }
        
        # MACD
        macd = self.calculate_macd(data)
        if macd is not None:
            macd_val = float(macd['macd'].iloc[-1])
            signal_val = float(macd['signal'].iloc[-1])
            hist_val = float(macd['histogram'].iloc[-1])
            
            result['macd'] = {
                'value': macd_val,
                'signal': signal_val,
                'histogram': hist_val,
                'trend': 'bullish' if macd_val > signal_val else 'bearish'
            }
        
        # Bollinger Bands
        bb = self.calculate_bollinger_bands(data)
        if bb is not None:
            current_price = float(data['Close'].iloc[-1])
            upper = float(bb['upper'].iloc[-1])
            middle = float(bb['middle'].iloc[-1])
            lower = float(bb['lower'].iloc[-1])
            
            # Determine position relative to bands
            if current_price > upper:
                position = 'above_upper'
            elif current_price < lower:
                position = 'below_lower'
            elif current_price > middle:
                position = 'upper_half'
            else:
                position = 'lower_half'
            
            result['bollinger_bands'] = {
                'upper': upper,
                'middle': middle,
                'lower': lower,
                'position': position
            }
        
        # EMAs
        for period in [20, 50, 200]:
            ema = self.calculate_ema(data, period)
            if ema is not None and len(ema) >= 2:
                result[f'ema_{period}'] = {
                    'value': float(ema.iloc[-1]),
                    'previous': float(ema.iloc[-2]),
                    'trend': 'up' if ema.iloc[-1] > ema.iloc[-2] else 'down'
                }
        
        # OBV (needed for COMBO strategy)
        obv = self.calculate_obv(data)
        if obv is not None and len(obv) >= 2:
            result['obv'] = {
                'value': float(obv.iloc[-1]),
                'previous': float(obv.iloc[-2]),
                'trend': 'up' if obv.iloc[-1] > obv.iloc[-2] else 'down'
            }
        
        # Advanced indicators (only in advanced mode)
        if self.advanced_mode:
            
            # Stochastic
            stoch = self.calculate_stochastic(data)
            if stoch is not None:
                k_val = float(stoch['k'].iloc[-1])
                d_val = float(stoch['d'].iloc[-1])
                
                result['stochastic'] = {
                    'k': k_val,
                    'd': d_val,
                    'trend': 'bullish' if k_val > d_val else 'bearish'
                }
            
            # ATR
            atr = self.calculate_atr(data)
            if atr is not None and len(atr) >= 2:
                result['atr'] = {
                    'value': float(atr.iloc[-1]),
                    'previous': float(atr.iloc[-2]),
                    'trend': 'increasing' if atr.iloc[-1] > atr.iloc[-2] else 'decreasing'
                }
            
            # OBV
            obv = self.calculate_obv(data)
            if obv is not None and len(obv) >= 2:
                result['obv'] = {
                    'value': float(obv.iloc[-1]),
                    'previous': float(obv.iloc[-2]),
                    'trend': 'up' if obv.iloc[-1] > obv.iloc[-2] else 'down'
                }
            
            # Williams %R
            willr = self.calculate_williams_r(data)
            if willr is not None and len(willr) >= 2:
                result['williams_r'] = {
                    'value': float(willr.iloc[-1]),
                    'previous': float(willr.iloc[-2]),
                    'trend': 'up' if willr.iloc[-1] > willr.iloc[-2] else 'down'
                }
            
            # CCI
            cci = self.calculate_cci(data)
            if cci is not None and len(cci) >= 2:
                result['cci'] = {
                    'value': float(cci.iloc[-1]),
                    'previous': float(cci.iloc[-2]),
                    'trend': 'up' if cci.iloc[-1] > cci.iloc[-2] else 'down'
                }
            
            # ROC
            roc = self.calculate_roc(data)
            if roc is not None and len(roc) >= 2:
                result['roc'] = {
                    'value': float(roc.iloc[-1]),
                    'previous': float(roc.iloc[-2]),
                    'trend': 'up' if roc.iloc[-1] > roc.iloc[-2] else 'down'
                }
        
        logger.info(f"Calculated {len(result)} indicators")
        return result
