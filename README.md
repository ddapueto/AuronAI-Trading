# AuronAI Trading System

Sistema de trading algorítmico profesional en Python con análisis técnico avanzado, risk management, backtesting, y un laboratorio visual para desarrollo de estrategias cuantitativas.

## ✨ Features

### Core Trading System
- 15+ indicadores técnicos (RSI, MACD, Bollinger Bands, EMAs, Stochastic, ATR, OBV, etc.)
- Risk management profesional con Kelly Criterion y stops dinámicos
- Análisis AI con Claude API para recomendaciones inteligentes
- Múltiples modos: demo (sin internet), paper trading, live trading
- Integración con Alpaca API para ejecución de trades

### 🆕 Swing Strategy Lab (NEW!)
- **Laboratorio visual interactivo** para desarrollo de estrategias cuantitativas
- **3 estrategias pre-construidas**: Long Momentum, Short Momentum, Neutral
- **Detección automática de régimen**: Bull/Bear/Neutral markets
- **Backtesting completo** con métricas profesionales (Sharpe, Calmar, Win Rate, etc.)
- **Visualización interactiva** con gráficos de equity curves y análisis de trades
- **Comparación de estrategias** lado a lado
- **Persistencia de datos** con Parquet y DuckDB para performance óptimo
- **UI web moderna** con Streamlit

## 🚀 Quick Start

### Opción 1: Swing Strategy Lab (Recomendado)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Lanzar la aplicación web
./scripts/run_streamlit_app.sh

# O manualmente
streamlit run src/auronai/ui/app.py
```

La aplicación se abrirá en `http://localhost:8501`

**Primeros pasos:**
1. Ve a "🚀 Run Backtest"
2. Selecciona una estrategia (Long Momentum recomendado)
3. Configura parámetros y haz clic en "Run Backtest"
4. Explora resultados en "📊 View Results"
5. Compara múltiples runs en "🔍 Compare Runs"

### Opción 2: Trading Agent Clásico

```bash
# Demo sin internet (recomendado para empezar)
python examples/demo_simulado.py

# Análisis con datos reales
python src/trading_agent.py

# Backtesting de estrategias específicas
python scripts/run_swing_multi_asset_v2.py
```

## 📚 Documentation

### Para Usuarios
- [Guía de Inicio Rápido](docs/user/INICIO_RAPIDO.md) - Empieza aquí
- [Swing Strategy Lab Guide](docs/user/swing-lab-guide.md) - **Guía completa del laboratorio**
- [Manual Completo](docs/user/GUIA_PRO.md) - Documentación detallada del trading agent
- [Estrategias Explicadas](docs/user/estrategia-alternada-explicada.md)
- **[Long Momentum Strategy](docs/user/estrategia-long-momentum.md)** - Estrategia real y aplicable
- [Implementación Real de Long Momentum](docs/user/long-momentum-implementacion-real.md) - Casos de uso prácticos
- **[Próximos Pasos Recomendados](docs/user/proximos-pasos-recomendados.md)** - ¿Qué hacer ahora?

### Para Desarrolladores
- [Arquitectura del Swing Lab](docs/technical/swing-lab-architecture.md) - **Arquitectura técnica**
- [Documentación Técnica](docs/technical/) - APIs y componentes
- [Decisiones de Diseño](docs/decisions/) - ADRs
- **[Roadmap Estratégico 2026](docs/decisions/009-roadmap-estrategico-2026.md)** - Plan de desarrollo

## 🏗️ Project Structure

```
AuronAI/
├── src/auronai/
│   ├── agents/           # Trading agents
│   ├── strategies/       # Strategy implementations (NEW!)
│   ├── backtesting/      # Backtest engine (NEW!)
│   ├── data/             # Data layer (Parquet, DuckDB) (NEW!)
│   ├── ui/               # Streamlit UI (NEW!)
│   ├── indicators/       # Technical indicators
│   ├── risk/             # Risk management
│   └── analysis/         # AI analysis
├── docs/
│   ├── user/             # User documentation
│   ├── technical/        # Technical documentation
│   └── decisions/        # Architecture Decision Records
├── examples/             # Usage examples
├── scripts/              # Utility scripts
├── tests/                # Test suite
└── data/
    ├── cache/            # Cached market data (NEW!)
    └── runs.db           # Backtest runs database (NEW!)
```

## 🎯 Use Cases

### 1. Desarrollo de Estrategias Cuantitativas
Usa el Swing Strategy Lab para:
- Probar ideas de trading rápidamente
- Comparar diferentes enfoques
- Optimizar parámetros
- Validar robustez en diferentes períodos

### 2. Análisis de Mercado
Usa el Trading Agent para:
- Análisis técnico detallado
- Recomendaciones AI con Claude
- Generación de planes de trade
- Monitoreo de múltiples símbolos

### 3. Backtesting Profesional
- Métricas completas (Sharpe, Calmar, Max DD, Win Rate, etc.)
- Análisis por régimen de mercado
- Comparación de estrategias
- Exportación de resultados

## 🔧 Requirements

- Python 3.11+
- API keys opcionales:
  - Claude API (Anthropic) - Para análisis AI
  - Alpaca API - Para trading execution

## License

[Tu licencia aquí]
