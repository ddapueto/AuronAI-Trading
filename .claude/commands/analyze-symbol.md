# /analyze-symbol — Analizar un símbolo de trading

Analiza el símbolo proporcionado como argumento: $ARGUMENTS

## Instrucciones

1. Busca información actual del símbolo en la web (precio, noticias recientes, earnings)
2. Lee los indicadores técnicos disponibles en `src/auronai/indicators/technical_indicators.py`
3. Proporciona un análisis completo en español:

### Análisis a generar:
- **Precio actual** y cambio del día
- **Tendencia**: Alcista/Bajista/Lateral (basado en EMAs 20/50/200)
- **Momentum**: RSI, MACD, Stochastic (sobrecompra/sobreventa)
- **Volatilidad**: ATR, Bollinger Bands (squeeze o expansión)
- **Volumen**: OBV tendencia, volumen vs promedio
- **Soporte/Resistencia**: Niveles clave
- **Régimen de mercado**: BULL/BEAR/NEUTRAL
- **Señal**: BUY / SELL / HOLD con confianza (1-10)
- **Setup de trade** (si hay señal):
  - Entry price
  - Stop Loss (basado en ATR)
  - Take Profit (risk/reward 2:1 mínimo)
  - Position size para cuenta de $3K (riesgo 1-2%)

### Formato de salida
Usa tablas markdown y sé conciso. Incluye advertencia de que es análisis técnico, no financial advice.
