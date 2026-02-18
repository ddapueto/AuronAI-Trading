# /market-scan — Escaneo de mercado

Escanea el mercado buscando oportunidades de trading.

Argumentos opcionales: $ARGUMENTS (sector, tipo de scan, timeframe)

## Instrucciones

1. Lee el symbol universe en `src/auronai/data/symbol_universe.py`
2. Busca en la web información actual del mercado:
   - Estado de SPY, QQQ, IWM (tendencia general)
   - VIX (nivel de miedo/avaricia)
   - Sectores con mejor/peor performance
3. Identifica oportunidades en estas categorías:

### Tipos de scan:
- **Momentum**: Símbolos con RSI entre 50-70, MACD bullish, precio > EMA20 > EMA50
- **Sobreventa**: RSI < 30, precio cerca de Bollinger inferior, en tendencia alcista mayor
- **Breakout**: Precio rompiendo resistencia con volumen > 2x promedio
- **Gap**: Gaps significativos (>2%) en el pre-market

### Output:
Para cada oportunidad encontrada:
```
Símbolo: XXXX
Setup: [Momentum/Sobreventa/Breakout/Gap]
Entry: $XX.XX
Stop Loss: $XX.XX
Take Profit: $XX.XX
Risk/Reward: X:1
Position Size: XX acciones ($XXX para cuenta $3K, riesgo 1%)
Confianza: X/10
```

### Reglas:
- Máximo 5 oportunidades
- Solo símbolos con volumen diario > 1M
- Risk/Reward mínimo 2:1
- Advertencia: análisis técnico, no financial advice
