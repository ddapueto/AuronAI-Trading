# FAQ - Long Momentum Strategy

## Preguntas Frecuentes sobre la Estrategia Long Momentum

### General

#### ¿Es Long Momentum una estrategia real o solo teórica?

**100% real.** Long Momentum es una de las estrategias más estudiadas en finanzas cuantitativas:
- Documentada académicamente desde 1993 (Jegadeesh & Titman)
- Usada por fondos institucionales (AQR, DFA, etc.)
- Disponible en ETFs comerciales (MTUM, PDP, SPMO)
- Miles de millones de dólares gestionados con esta estrategia

#### ¿Cuánto capital necesito para empezar?

**Mínimo recomendado: $10,000 USD**

Razones:
- Necesitas diversificar en al menos 3 símbolos
- Costos de transacción deben ser < 1% del capital
- Con menos capital, las comisiones erosionan las ganancias

Alternativas con menos capital:
- $5,000: Usa ETFs en lugar de acciones individuales
- $1,000-5,000: Paper trading primero, acumula capital

#### ¿Qué retorno puedo esperar?

**Retorno esperado: +15-25% anual** (basado en backtests históricos)

Pero considera:
- Variabilidad alta: Algunos años +40%, otros +5%
- Drawdowns de -15 a -25% son normales
- Solo opera ~60% del tiempo (cuando es BULL)
- Resultados pasados no garantizan resultados futuros

Comparación:
- S&P 500: ~10% anual promedio
- Long Momentum: ~20% anual promedio
- Alpha: ~10% anual (exceso sobre mercado)

---

### Implementación

#### ¿Necesito programar para usar esta estrategia?

**No necesariamente.** Tienes 3 opciones:

1. **Manual** (sin programación):
   - Usa AuronAI para generar señales
   - Ejecuta trades manualmente en tu broker
   - Tiempo: 30-45 min/semana

2. **Semi-automatizada** (programación básica):
   - Ejecuta scripts de Python
   - Revisa señales y ejecuta manualmente
   - Tiempo: 15-20 min/semana

3. **Automatizada** (programación avanzada):
   - Integración con broker API
   - Ejecución automática
   - Tiempo: 5-10 min/semana (monitoreo)

#### ¿Qué broker debo usar?

**Recomendaciones por nivel:**

**Principiante**: TD Ameritrade
- ✅ Interfaz amigable
- ✅ $0 comisiones
- ✅ Excelente soporte
- ❌ No tiene API

**Intermedio**: Interactive Brokers
- ✅ Comisiones bajas
- ✅ API disponible
- ✅ Acceso global
- ❌ Interfaz compleja

**Avanzado**: Alpaca
- ✅ API-first (automatización)
- ✅ $0 comisiones
- ✅ Ejecución rápida
- ❌ Solo mercado US

**Evitar**:
- Brokers con comisiones altas (>$5 por trade)
- Brokers sin acceso a mercado US
- Brokers con ejecución lenta

#### ¿Cuánto tiempo requiere por semana?

**Depende del nivel de automatización:**

**Manual**: 30-45 minutos/semana
- Lunes: 35 min (rebalanceo)
- Martes-Viernes: 5 min/día (monitoreo)

**Semi-automatizada**: 15-20 minutos/semana
- Lunes: 15 min (revisar señales y ejecutar)
- Martes-Viernes: 2 min/día (alertas)

**Automatizada**: 5-10 minutos/semana
- Monitoreo de alertas
- Revisión de performance

---

### Riesgos

#### ¿Cuál es el mayor riesgo de esta estrategia?

**Momentum Crashes** - Reversiones bruscas del momentum

Ejemplo histórico:
- Marzo 2020 (COVID): Momentum cayó -30% en 2 semanas
- Dot-com crash (2000): Momentum cayó -40% en 3 meses
- 2008 Financial Crisis: Momentum cayó -50%

**Mitigación**:
- Filtro de régimen (solo opera en BULL)
- Stops automáticos (trend reversal)
- Exposición limitada (20% máximo)
- Diversificación (3-5 posiciones)

Aún así, **no elimina el riesgo completamente**.

#### ¿Puedo perder todo mi dinero?

**Técnicamente sí, pero muy improbable** con gestión de riesgo adecuada.

Escenario de pérdida total requeriría:
- Ignorar todos los stops
- Concentración en 1 símbolo
- Símbolo va a $0 (quiebra)
- No salir del mercado en crash

Con gestión de riesgo de AuronAI:
- Exposición máxima: 20%
- Pérdida máxima realista: -15 a -25% del portfolio total
- Pérdida catastrófica: -40% (extremadamente raro)

#### ¿Qué pasa si el mercado cae?

**La estrategia sale a cash automáticamente.**

Proceso:
1. Régimen cambia de BULL a BEAR/NEUTRAL
2. Estrategia vende todas las posiciones
3. Portfolio queda 100% en cash
4. Espera a que régimen vuelva a BULL

Ejemplo:
- 2022 (Bear Market): Estrategia en cash → 0% retorno
- S&P 500: -18% retorno
- Resultado: Protección de capital

---

### Parámetros

#### ¿Qué significan los parámetros?

**top_k** (default: 3)
- Número de posiciones simultáneas
- Más alto = Más diversificación, menos retorno
- Más bajo = Menos diversificación, más retorno
- Rango recomendado: 3-5

**holding_days** (default: 10)
- Días objetivo de tenencia
- Más alto = Menos trades, menos costos
- Más bajo = Más trades, más costos
- Rango recomendado: 7-14

**tp_multiplier** (default: 1.05 = +5%)
- Take profit objetivo
- Más alto = Más ganancia por trade, menos win rate
- Más bajo = Menos ganancia por trade, más win rate
- Rango recomendado: 1.03-1.07

**risk_budget** (default: 0.20 = 20%)
- Exposición máxima del portfolio
- Más alto = Más retorno, más riesgo
- Más bajo = Menos retorno, menos riesgo
- Rango recomendado: 0.15-0.30

#### ¿Debo optimizar los parámetros?

**Sí, pero con cuidado.**

✅ **Hacer**:
- Backtest con diferentes parámetros
- Elegir los que funcionan en múltiples períodos
- Validar con walk-forward analysis
- Mantener por al menos 3 meses antes de cambiar

❌ **No hacer**:
- Optimizar solo en un período (overfitting)
- Cambiar parámetros cada semana
- Buscar el "parámetro perfecto"
- Ignorar costos de transacción

**Proceso recomendado**:
```bash
# 1. Backtest con diferentes parámetros
python scripts/optimize_parameters.py

# 2. Validar con walk-forward
python scripts/run_walk_forward_validation.py

# 3. Elegir parámetros robustos
# 4. Mantener por 3-6 meses
# 5. Re-evaluar y ajustar si es necesario
```

---

### Performance

#### ¿Por qué mi performance es diferente al backtest?

**Razones comunes:**

1. **Costos de transacción**
   - Backtest: Asume 0.05% slippage
   - Real: Puede ser 0.1-0.2% con broker malo

2. **Timing de ejecución**
   - Backtest: Asume ejecución instantánea
   - Real: Delay de segundos/minutos

3. **Período diferente**
   - Backtest: Datos históricos
   - Real: Mercado actual (puede ser diferente)

4. **Errores de implementación**
   - No seguir señales exactamente
   - Override manual de decisiones
   - Configuración incorrecta

**Solución**:
- Documenta todos los trades
- Compara con señales generadas
- Identifica discrepancias
- Ajusta proceso

#### ¿Cuánto tiempo tarda en funcionar?

**Mínimo 3-6 meses para evaluar.**

Razones:
- Variabilidad de corto plazo es alta
- Necesitas múltiples ciclos de mercado
- Algunos meses serán malos, otros buenos

Ejemplo:
```
Mes 1: +5%  ✅
Mes 2: -3%  ❌
Mes 3: +8%  ✅
Mes 4: +2%  ✅
Mes 5: -1%  ❌
Mes 6: +6%  ✅
────────────────
Total: +17% ✅ (vs +10% del S&P 500)
```

**No juzgues por 1-2 meses.**

#### ¿Qué win rate debo esperar?

**Win rate esperado: 50-60%**

Esto significa:
- 5-6 trades ganadores de cada 10
- 4-5 trades perdedores de cada 10

**Esto es NORMAL y SALUDABLE.**

Lo importante no es el win rate, sino el **profit factor**:
```
Profit Factor = Ganancias totales / Pérdidas totales

Objetivo: > 1.5

Ejemplo:
- 6 trades ganadores: +$600 ($100 cada uno)
- 4 trades perdedores: -$200 ($50 cada uno)
- Profit Factor: $600 / $200 = 3.0 ✅
```

---

### Comparación con Otras Estrategias

#### ¿Es mejor que buy-and-hold?

**Depende del período y tus objetivos.**

**Ventajas vs Buy-and-Hold**:
- ✅ Mejor retorno ajustado por riesgo (Sharpe ratio)
- ✅ Menor drawdown máximo
- ✅ Protección en bear markets (sale a cash)
- ✅ Más activo (para quienes disfrutan trading)

**Desventajas vs Buy-and-Hold**:
- ❌ Más trabajo (monitoreo semanal)
- ❌ Costos de transacción
- ❌ Impuestos de corto plazo (más altos)
- ❌ Requiere disciplina

**Veredicto**: 
- Para inversores pasivos: Buy-and-hold
- Para traders activos: Long Momentum

#### ¿Puedo combinarla con otras estrategias?

**¡Sí! Es altamente recomendado.**

**Combinaciones efectivas**:

1. **Long Momentum + Short Momentum**
   - Long en BULL, Short en BEAR
   - Cobertura completa del ciclo
   - Retorno más consistente

2. **Long Momentum + Mean Reversion**
   - Momentum para tendencias
   - Mean Reversion para reversiones
   - Diversificación de estilos

3. **Long Momentum + Value**
   - Momentum para crecimiento
   - Value para protección
   - Factores complementarios

**Ejemplo de portfolio balanceado**:
```
50% Long Momentum (BULL)
30% Short Momentum (BEAR)
20% Mean Reversion (NEUTRAL)
────────────────────────────
= Portfolio all-weather
```

---

### Problemas Comunes

#### Las señales no coinciden con mi análisis manual

**Esto es normal y esperado.**

Razones:
- Estrategia usa reglas objetivas
- Tu análisis incluye subjetividad
- Diferentes indicadores/timeframes

**¿Qué hacer?**
1. Confía en el proceso (al menos 3 meses)
2. Si persiste, revisa tu análisis
3. Considera que la estrategia puede estar correcta

**No hagas**: Override las señales por "intuición"

#### La estrategia no genera señales

**Posibles causas:**

1. **Régimen no es BULL**
   - Solución: Espera a que mercado mejore
   - Verifica: `python main.py --mode regime-check`

2. **Ningún símbolo pasa filtros**
   - Solución: Amplía universo de símbolos
   - Verifica: Revisa criterios (EMA20>50, RSI<70)

3. **Datos faltantes**
   - Solución: Actualiza cache de datos
   - Verifica: `python scripts/check_data_availability.py`

#### Los costos son muy altos

**Optimizaciones:**

1. **Reduce frecuencia de rebalanceo**
   - Semanal → Quincenal
   - Impacto: -50% costos, -5% retorno

2. **Aumenta capital**
   - $10K → $50K
   - Impacto: Costos de 0.5% → 0.1%

3. **Cambia de broker**
   - Broker con comisiones → Broker $0
   - Impacto: Ahorro inmediato

4. **Aumenta holding_days**
   - 10 días → 14 días
   - Impacto: -30% trades, -30% costos

---

### Aspectos Legales y Fiscales

#### ¿Debo pagar impuestos?

**Sí, en la mayoría de jurisdicciones.**

**Tipos de impuestos:**

1. **Ganancias de Capital**
   - Corto plazo (< 1 año): Tasa alta (como ingreso ordinario)
   - Largo plazo (> 1 año): Tasa reducida
   - Long Momentum: Principalmente corto plazo

2. **Dividendos**
   - Si las acciones pagan dividendos
   - Generalmente tasa reducida

**Ejemplo (USA)**:
```
Ganancia: $10,000
Holding: < 1 año (corto plazo)
Tasa: 24% (bracket típico)
Impuesto: $2,400
Ganancia neta: $7,600
```

**Optimización fiscal**:
- Usa cuentas con ventajas fiscales (IRA, 401k)
- Considera tax-loss harvesting
- Consulta con contador

#### ¿Es legal el trading algorítmico?

**Sí, es completamente legal** en la mayoría de países.

**Requisitos:**
- Usar broker regulado
- Reportar ganancias/pérdidas
- No manipular mercado
- No usar información privilegiada

**No es legal**:
- Spoofing (órdenes falsas)
- Front-running
- Insider trading
- Manipulación de precios

Long Momentum no hace nada de esto, es 100% legal.

---

### Soporte

#### ¿Dónde puedo obtener ayuda?

**Recursos:**

1. **Documentación**
   - [Guía Completa](estrategia-long-momentum.md)
   - [Implementación Real](long-momentum-implementacion-real.md)
   - [Documentación Técnica](../technical/)

2. **Scripts de Ayuda**
   ```bash
   # Demo interactivo
   python scripts/demo_long_momentum.py
   
   # Verificar configuración
   python scripts/check_setup.py
   
   # Diagnóstico de problemas
   python scripts/diagnose.py
   ```

3. **Comunidad**
   - Discord: [Link]
   - GitHub Issues: [Link]
   - Reddit: r/algotrading

4. **Soporte Profesional**
   - Email: support@auronai.com
   - Consultoría: [Link]

#### ¿Puedo contribuir al proyecto?

**¡Sí! Contribuciones son bienvenidas.**

**Formas de contribuir:**

1. **Código**
   - Mejoras a estrategias
   - Nuevos indicadores
   - Optimizaciones de performance

2. **Documentación**
   - Tutoriales
   - Traducciones
   - Ejemplos de uso

3. **Testing**
   - Reportar bugs
   - Validar en diferentes mercados
   - Compartir resultados

4. **Comunidad**
   - Responder preguntas
   - Compartir experiencias
   - Crear contenido educativo

Ver: [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

## ¿Más Preguntas?

Si tu pregunta no está aquí:

1. Revisa la [documentación completa](estrategia-long-momentum.md)
2. Busca en [GitHub Issues](https://github.com/tu-repo/AuronAI/issues)
3. Pregunta en [Discord](https://discord.gg/tu-server)
4. Crea un nuevo issue en GitHub

**Recuerda**: No hay preguntas tontas. Todos empezamos desde cero.
