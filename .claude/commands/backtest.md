# /backtest — Ejecutar backtest de una estrategia

Ejecuta un backtest de la estrategia indicada: $ARGUMENTS

## Instrucciones

1. Lee las estrategias disponibles en `src/auronai/strategies/`
2. Lee el BacktestRunner en `src/auronai/backtesting/backtest_runner.py`
3. Identifica la estrategia solicitada
4. Ejecuta el backtest correspondiente usando los scripts en `scripts/`
5. Presenta los resultados en formato tabla:

### Métricas a reportar:
| Métrica | Valor |
|---|---|
| Retorno Total | X% |
| Retorno Anualizado | X% |
| Sharpe Ratio | X.XX |
| Sortino Ratio | X.XX |
| Max Drawdown | -X% |
| Win Rate | X% |
| Profit Factor | X.XX |
| Total Trades | N |

### Si no se especifica estrategia:
Listar las estrategias disponibles con descripción breve:
- Long Momentum
- Short Momentum
- Dual Momentum
- Swing TP
- Neutral

Preguntar cuál quiere ejecutar.
