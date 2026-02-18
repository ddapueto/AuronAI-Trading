# Scripts de AuronAI

Scripts de utilidad para ejecutar backtests y análisis.

## Swing Baseline Strategy

### Prueba Rápida (Recomendado para empezar)

```bash
python scripts/test_swing_baseline_quick.py
```

Ejecuta un backtest corto (3 meses, 2 símbolos) para verificar que todo funciona.

### Backtest Completo

```bash
python scripts/run_swing_baseline_backtest.py
```

Ejecuta el backtest completo:
- Símbolos: AAPL, TSLA, MSFT, NVDA, GOOGL
- Período: 2024-01-01 a 2026-01-31
- Test period: 2025-07-01 a 2026-01-31
- Capital: $1,000

Genera:
- `results/swing_baseline_results.json` - Resultados completos
- `results/swing_baseline_trades.csv` - Tabla de trades
- `results/equity_curve.png` - Gráfico de equity curve

### Comparación Con/Sin Protecciones

```bash
python scripts/compare_baseline_strategies.py
```

Compara dos versiones:
1. Baseline sin protecciones (siempre 20%, siempre 5 símbolos)
2. Baseline mejorada (con market regime filter, kill switch, etc.)

Genera:
- `results/baseline_no_protection.json`
- `results/baseline_with_protection.json`
- `results/comparison_equity_curves.png`

## Requisitos

Asegúrate de tener instaladas las dependencias:

```bash
pip install yfinance pandas pandas-ta numpy matplotlib
```

O instala todo el proyecto:

```bash
pip install -e .
```

## Documentación

Ver [Swing Baseline Strategy](../docs/user/swing-baseline-strategy.md) para documentación completa.
