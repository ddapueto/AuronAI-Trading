# /team — Ver agentes disponibles del proyecto

Muestra el equipo de agentes y skills disponibles.

## Instrucciones

Listar todos los agentes y skills del proyecto con descripción breve.

### Agentes (`.claude/agents/`)

| Agente | Rol | Sprints |
|---|---|---|
| **trading-expert** | Análisis de mercado, educación, recomendaciones | Todos |
| **code-reviewer** | Code review especializado en trading systems | Todos |
| **backend-dev** | Desarrollo Python: brokers, API, pipeline | 1, 4, 7 |
| **test-engineer** | QA: unit tests, integration, trading checks | Todos |
| **data-engineer** | Datos: símbolos, indicadores, features, streaming | 3, 4, 5, 6 |
| **strategy-dev** | Estrategias: implementación, backtest, validación | 2, 3, 5 |
| **ml-engineer** | ML: feature engineering, XGBoost, FinBERT | 6 |
| **devops** | Infra: Docker, CI/CD, dependencias | 1, transversal |

### Skills (`.claude/commands/`)

| Skill | Uso |
|---|---|
| `/analyze-symbol AAPL` | Analizar un símbolo de trading |
| `/backtest dual_momentum` | Ejecutar backtest de una estrategia |
| `/market-scan momentum` | Escanear mercado buscando oportunidades |
| `/learn-strategy turtle` | Aprender una estrategia en detalle |
| `/risk-check AAPL 150 145 160` | Verificar riesgo de un trade |
| `/implement 18` | Implementar un issue de GitHub |
| `/test all` | Correr tests con coverage |
| `/qa` | QA completo de cierre de sprint |
| `/sprint-status` | Ver estado del sprint actual |
| `/review` | Code review de cambios actuales |
| `/lint fix` | Linting + type checking |
| `/deploy docker` | Build y deploy infraestructura |
| `/team` | Este listado |
