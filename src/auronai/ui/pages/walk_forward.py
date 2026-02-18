"""
Walk-Forward Optimization page for Streamlit UI.

This page allows users to run rolling walk-forward optimization
with visual progress tracking and comprehensive results display.
"""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from auronai.backtesting.rolling_walk_forward import RollingWalkForwardOptimizer
from auronai.utils.logger import get_logger

logger = get_logger(__name__)


def show():
    """Display walk-forward optimization page."""
    
    st.title("🔄 Rolling Walk-Forward Optimization")
    
    st.markdown("""
    Rolling walk-forward simula trading real re-optimizando parámetros periódicamente.
    
    **¿Cómo funciona?**
    1. Optimiza parámetros usando datos históricos (ej: últimos 6 meses)
    2. Opera con esos parámetros durante un período (ej: 1 semana)
    3. Re-optimiza la siguiente semana con datos actualizados
    4. Repite durante todo el período de prueba
    
    **Ventajas**:
    - ✅ Simula trading real (re-optimización periódica)
    - ✅ Detecta overfitting (degradación in-sample vs out-of-sample)
    - ✅ Resultados más realistas que backtest simple
    """)
    
    st.markdown("---")
    
    # Configuration section
    st.header("⚙️ Configuración")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Estrategia y Símbolos")
        
        strategy_name = st.selectbox(
            "Estrategia",
            ["long_momentum", "short_momentum", "neutral"],
            help="Estrategia a optimizar"
        )
        
        # Symbol selection
        available_symbols = [
            "AAPL", "MSFT", "GOOGL", "NVDA", "TSLA",
            "AMZN", "META", "NFLX", "AMD", "INTC"
        ]
        
        symbols = st.multiselect(
            "Símbolos",
            available_symbols,
            default=["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"],
            help="Selecciona 3-10 símbolos para diversificación"
        )
        
        if len(symbols) < 3:
            st.warning("⚠️ Recomendado: Selecciona al menos 3 símbolos")
        
        st.subheader("Período de Análisis")
        
        start_date = st.date_input(
            "Fecha Inicio",
            value=datetime(2020, 1, 1),
            min_value=datetime(2015, 1, 1),
            max_value=datetime.now(),
            help="Inicio del período de walk-forward"
        )
        
        end_date = st.date_input(
            "Fecha Fin",
            value=datetime(2025, 12, 31),
            min_value=start_date,
            max_value=datetime.now(),
            help="Fin del período de walk-forward"
        )
    
    with col2:
        st.subheader("Ventanas de Optimización")
        
        train_window_days = st.number_input(
            "Ventana de Entrenamiento (días)",
            min_value=30,
            max_value=365,
            value=180,
            step=30,
            help="Días de datos históricos para optimizar (recomendado: 180 = 6 meses)"
        )
        
        test_window_days = st.number_input(
            "Ventana de Prueba (días)",
            min_value=1,
            max_value=30,
            value=7,
            step=1,
            help="Días para probar con parámetros optimizados (recomendado: 7 = 1 semana)"
        )
        
        reoptimize_frequency = st.selectbox(
            "Frecuencia de Re-optimización",
            ["weekly", "monthly"],
            index=0,
            help="Cada cuánto re-optimizar parámetros"
        )
        
        st.subheader("Capital y Costos")
        
        initial_capital = st.number_input(
            "Capital Inicial ($)",
            min_value=1000.0,
            max_value=1000000.0,
            value=10000.0,
            step=1000.0,
            help="Capital inicial para cada backtest"
        )
        
        commission_rate = st.number_input(
            "Comisión (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.01,
            format="%.3f",
            help="Comisión por trade (0.0 = broker gratuito)"
        )
        
        slippage_rate = st.number_input(
            "Slippage (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.05,
            step=0.01,
            format="%.3f",
            help="Slippage esperado (0.05% = realista para acciones líquidas)"
        )
    
    # Parameter grid section
    st.markdown("---")
    st.header("🎯 Grid de Parámetros")
    
    st.markdown("""
    Define los valores a probar para cada parámetro. El optimizador probará todas las combinaciones.
    
    **Tip**: Menos valores = más rápido, pero menos exhaustivo
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        top_k_values = st.multiselect(
            "top_k (posiciones simultáneas)",
            [2, 3, 4, 5, 6],
            default=[2, 3, 4, 5],
            help="Número de posiciones a mantener simultáneamente"
        )
    
    with col2:
        holding_days_values = st.multiselect(
            "holding_days (días de retención)",
            [5, 7, 10, 14, 21],
            default=[7, 10, 14],
            help="Días máximos para mantener una posición"
        )
    
    with col3:
        tp_multiplier_values = st.multiselect(
            "tp_multiplier (take profit)",
            [1.03, 1.05, 1.07, 1.10],
            default=[1.03, 1.05, 1.07],
            help="Multiplicador para take profit (1.05 = +5%)"
        )
    
    # Calculate expected time
    if symbols and top_k_values and holding_days_values and tp_multiplier_values:
        total_days = (datetime.combine(end_date, datetime.min.time()) - 
                     datetime.combine(start_date, datetime.min.time())).days
        
        if reoptimize_frequency == "weekly":
            expected_periods = total_days // 7
        else:
            expected_periods = total_days // 30
        
        combinations = len(top_k_values) * len(holding_days_values) * len(tp_multiplier_values)
        total_backtests = expected_periods * combinations
        estimated_minutes = total_backtests * 2 / 60  # ~2 seconds per backtest
        
        st.info(f"""
        📊 **Estimación**:
        - Períodos: ~{expected_periods}
        - Combinaciones por período: {combinations}
        - Total backtests: ~{total_backtests:,}
        - Tiempo estimado: ~{estimated_minutes:.0f} minutos ({estimated_minutes/60:.1f} horas)
        """)
    
    # Run button
    st.markdown("---")
    
    if st.button("🚀 Ejecutar Walk-Forward Optimization", type="primary", use_container_width=True):
        
        # Validation
        if not symbols:
            st.error("❌ Selecciona al menos 1 símbolo")
            return
        
        if not top_k_values or not holding_days_values or not tp_multiplier_values:
            st.error("❌ Selecciona al menos 1 valor para cada parámetro")
            return
        
        # Create param grid
        param_grid = {
            'top_k': top_k_values,
            'holding_days': holding_days_values,
            'tp_multiplier': tp_multiplier_values,
            'risk_budget': [0.20],  # Fixed
            'defensive_risk_budget': [0.05]  # Fixed
        }
        
        # Run optimization
        run_walk_forward_optimization(
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.min.time()),
            train_window_days=train_window_days,
            test_window_days=test_window_days,
            reoptimize_frequency=reoptimize_frequency,
            initial_capital=initial_capital,
            commission_rate=commission_rate / 100,  # Convert to decimal
            slippage_rate=slippage_rate / 100,  # Convert to decimal
            param_grid=param_grid
        )


def run_walk_forward_optimization(
    strategy_name: str,
    symbols: list,
    start_date: datetime,
    end_date: datetime,
    train_window_days: int,
    test_window_days: int,
    reoptimize_frequency: str,
    initial_capital: float,
    commission_rate: float,
    slippage_rate: float,
    param_grid: dict
):
    """Run walk-forward optimization with progress tracking."""
    
    st.markdown("---")
    st.header("🔄 Ejecutando Optimización...")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Create optimizer
        status_text.text("Inicializando optimizador...")
        
        optimizer = RollingWalkForwardOptimizer(
            train_window_days=train_window_days,
            test_window_days=test_window_days,
            reoptimize_frequency=reoptimize_frequency,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate
        )
        
        progress_bar.progress(5)
        
        # Run optimization
        status_text.text("Ejecutando walk-forward optimization... (esto puede tomar tiempo)")
        
        result = optimizer.run(
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            param_grid=param_grid
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Optimización completada!")
        
        # Display results
        display_results(result)
        
        # Save results
        save_results(result)
        
    except Exception as e:
        st.error(f"❌ Error durante optimización: {e}")
        logger.error(f"Walk-forward optimization error: {e}", exc_info=True)


def display_results(result):
    """Display walk-forward optimization results."""
    
    st.markdown("---")
    st.header("📊 Resultados")
    
    # Summary metrics
    st.subheader("Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Períodos Analizados",
            result.total_periods
        )
    
    with col2:
        st.metric(
            "Sharpe In-Sample",
            f"{result.avg_train_sharpe:.2f}"
        )
    
    with col3:
        st.metric(
            "Sharpe Out-of-Sample",
            f"{result.avg_test_sharpe:.2f}",
            delta=f"± {result.std_test_sharpe:.2f}"
        )
    
    with col4:
        degradation_color = "normal" if result.degradation < 0.30 else "inverse"
        st.metric(
            "Degradación",
            f"{result.degradation:.1%}",
            delta=None,
            delta_color=degradation_color
        )
    
    # Degradation interpretation
    if result.degradation < 0.20:
        st.success("✅ **Excelente**: Estrategia muy robusta (< 20% degradación)")
    elif result.degradation < 0.30:
        st.success("✅ **Buena**: Estrategia robusta (< 30% degradación)")
    elif result.degradation < 0.40:
        st.warning("⚠️ **Aceptable**: Algo de sobreajuste (30-40% degradación)")
    else:
        st.error("❌ **Mala**: Mucho sobreajuste (> 40% degradación)")
    
    # Performance metrics
    st.markdown("---")
    st.subheader("Métricas de Performance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Retorno Promedio (por período)",
            f"{result.avg_test_return:.2%}"
        )
        
        # Annualized return estimate
        if result.reoptimize_frequency == "weekly":
            periods_per_year = 52
        else:
            periods_per_year = 12
        
        annualized_return = result.avg_test_return * periods_per_year
        st.caption(f"Retorno anualizado estimado: {annualized_return:.1%}")
    
    with col2:
        st.metric(
            "Max Drawdown Promedio",
            f"{result.avg_test_max_dd:.2%}"
        )
    
    with col3:
        st.metric(
            "Desviación Estándar (Sharpe)",
            f"{result.std_test_sharpe:.2f}"
        )
        
        if result.std_test_sharpe < 0.5:
            st.caption("✅ Baja variabilidad")
        elif result.std_test_sharpe < 1.0:
            st.caption("⚠️ Variabilidad moderada")
        else:
            st.caption("❌ Alta variabilidad")
    
    # Parameter frequency
    st.markdown("---")
    st.subheader("Frecuencia de Parámetros")
    
    st.markdown("""
    Muestra qué valores de parámetros fueron elegidos más frecuentemente.
    Alta frecuencia (> 50%) indica parámetros estables y robustos.
    """)
    
    # Create DataFrame for parameter frequency
    param_freq_data = []
    for param, count in sorted(result.param_frequency.items(), key=lambda x: x[1], reverse=True):
        percentage = count / result.total_periods * 100
        param_freq_data.append({
            'Parámetro': param,
            'Veces Elegido': count,
            'Porcentaje': f"{percentage:.1f}%"
        })
    
    param_freq_df = pd.DataFrame(param_freq_data)
    st.dataframe(param_freq_df, use_container_width=True, hide_index=True)
    
    # Best and worst periods
    st.markdown("---")
    st.subheader("Mejor y Peor Período")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏆 Mejor Período**")
        st.write(f"Período: {result.best_period.period_id}")
        st.write(f"Test Sharpe: {result.best_period.test_sharpe:.2f}")
        st.write(f"Parámetros:")
        st.json({
            'top_k': result.best_period.best_params.top_k,
            'holding_days': result.best_period.best_params.holding_days,
            'tp_multiplier': f"{result.best_period.best_params.tp_multiplier:.3f}"
        })
    
    with col2:
        st.markdown("**📉 Peor Período**")
        st.write(f"Período: {result.worst_period.period_id}")
        st.write(f"Test Sharpe: {result.worst_period.test_sharpe:.2f}")
        st.write(f"Parámetros:")
        st.json({
            'top_k': result.worst_period.best_params.top_k,
            'holding_days': result.worst_period.best_params.holding_days,
            'tp_multiplier': f"{result.worst_period.best_params.tp_multiplier:.3f}"
        })
    
    # Period-by-period chart
    st.markdown("---")
    st.subheader("Performance por Período")
    
    plot_period_performance(result)
    
    # Detailed periods table
    with st.expander("📋 Ver Todos los Períodos"):
        periods_data = []
        for period in result.periods:
            periods_data.append({
                'Período': period.period_id,
                'Train Start': period.train_start.strftime('%Y-%m-%d'),
                'Train End': period.train_end.strftime('%Y-%m-%d'),
                'Test Start': period.test_start.strftime('%Y-%m-%d'),
                'Test End': period.test_end.strftime('%Y-%m-%d'),
                'Train Sharpe': f"{period.train_sharpe:.2f}",
                'Test Sharpe': f"{period.test_sharpe:.2f}",
                'Degradación': f"{((period.train_sharpe - period.test_sharpe) / period.train_sharpe * 100):.1f}%",
                'top_k': period.best_params.top_k,
                'holding_days': period.best_params.holding_days,
                'tp_multiplier': f"{period.best_params.tp_multiplier:.3f}"
            })
        
        periods_df = pd.DataFrame(periods_data)
        st.dataframe(periods_df, use_container_width=True, hide_index=True)


def plot_period_performance(result):
    """Plot performance metrics across periods."""
    
    # Prepare data
    period_ids = [p.period_id for p in result.periods]
    train_sharpes = [p.train_sharpe for p in result.periods]
    test_sharpes = [p.test_sharpe for p in result.periods]
    test_returns = [p.test_return * 100 for p in result.periods]  # Convert to percentage
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Sharpe Ratio por Período', 'Retorno por Período'),
        vertical_spacing=0.15
    )
    
    # Sharpe ratio plot
    fig.add_trace(
        go.Scatter(
            x=period_ids,
            y=train_sharpes,
            mode='lines+markers',
            name='Train Sharpe',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=period_ids,
            y=test_sharpes,
            mode='lines+markers',
            name='Test Sharpe',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    # Add average line
    fig.add_hline(
        y=result.avg_test_sharpe,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Avg: {result.avg_test_sharpe:.2f}",
        row=1, col=1
    )
    
    # Return plot
    fig.add_trace(
        go.Bar(
            x=period_ids,
            y=test_returns,
            name='Test Return (%)',
            marker=dict(
                color=test_returns,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Return %", y=0.25, len=0.4)
            )
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_xaxes(title_text="Período", row=2, col=1)
    fig.update_yaxes(title_text="Sharpe Ratio", row=1, col=1)
    fig.update_yaxes(title_text="Return (%)", row=2, col=1)
    
    fig.update_layout(
        height=700,
        showlegend=True,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def save_results(result):
    """Save walk-forward results to file."""
    
    # Create output directory
    output_dir = Path("results/walk_forward")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{result.strategy_name}_wf_{timestamp}.json"
    output_file = output_dir / filename
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    st.success(f"✅ Resultados guardados en: `{output_file}`")
    
    # Download button
    with open(output_file, 'r') as f:
        st.download_button(
            label="📥 Descargar Resultados (JSON)",
            data=f.read(),
            file_name=filename,
            mime="application/json"
        )

