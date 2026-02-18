# /risk-check — Verificar gestión de riesgo

Evalúa el estado de riesgo del portfolio o de un trade específico: $ARGUMENTS

## Instrucciones

### Si se proporciona un trade:
Formato esperado: `SYMBOL ENTRY STOP_LOSS TAKE_PROFIT` o `SYMBOL ENTRY STOP_LOSS`

Calcular:
- **Risk por acción**: Entry - Stop Loss
- **Position size (1% risk)**: ($3,000 × 0.01) / risk_por_accion
- **Position size (2% risk)**: ($3,000 × 0.02) / risk_por_accion
- **Valor de la posición**: Position size × Entry price
- **% del portfolio**: Valor posición / $3,000
- **Risk/Reward ratio**: (TP - Entry) / (Entry - SL)
- **Evaluación**: APROBAR / RECHAZAR con razón

### Reglas de aprobación:
- Risk/Reward >= 2:1 → OK
- Risk/Reward 1.5-2:1 → Advertencia
- Risk/Reward < 1.5:1 → RECHAZAR
- Posición > 33% del portfolio → Advertencia
- Posición > 50% del portfolio → RECHAZAR

### Si no se proporciona trade:
Mostrar reglas de gestión de riesgo para la cuenta:
```
Capital: $3,000
Riesgo max por trade (1%): $30
Riesgo max por trade (2%): $60
Max posiciones simultáneas: 2-3
Drawdown diario max (3%): $90
Drawdown semanal max (5%): $150
Day trades disponibles (PDT): 3 en 5 días rolling
```

Lee `src/auronai/risk/risk_manager.py` para contexto adicional.
