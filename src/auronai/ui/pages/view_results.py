"""
View Results page.

Displays detailed backtest results including charts, metrics, and trades.

**Validates: Requirements FR-16**
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from auronai.backtesting import RunManager


def show():
    """Display the View Results page."""
    
    st.title("📊 View Results")
    st.markdown("Analyze backtest results in detail.")
    st.markdown("---")
    
    # Check if there's a result in session state
    if 'last_run_id' in st.session_state:
        run_id = st.session_state['last_run_id']
        st.info(f"Showing results for most recent run: `{run_id}`")
    else:
        st.warning("No backtest results available. Please run a backtest first.")
        return
    
    # Load run from database
    run_manager = RunManager(db_path="data/runs.db")
    run = run_manager.get_run(run_id)
    
    if not run:
        st.error(f"Could not load run {run_id}")
        run_manager.close()
        return
    
    # Display metrics
    st.subheader("📈 Performance Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Return",
            f"{run.metrics.get('total_return', 0):.2%}"
        )
    
    with col2:
        st.metric(
            "CAGR",
            f"{run.metrics.get('cagr', 0):.2%}"
        )
    
    with col3:
        st.metric(
            "Sharpe Ratio",
            f"{run.metrics.get('sharpe_ratio', 0):.2f}"
        )
    
    with col4:
        st.metric(
            "Max Drawdown",
            f"{run.metrics.get('max_drawdown', 0):.2%}"
        )
    
    with col5:
        st.metric(
            "Win Rate",
            f"{run.metrics.get('win_rate', 0):.2%}"
        )
    
    st.markdown("---")
    
    # Equity curve
    st.subheader("💰 Equity Curve")
    
    equity_df = run_manager.get_equity_curve(run_id)
    
    if not equity_df.empty:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(equity_df['date']),
            y=equity_df['equity'],
            mode='lines',
            name='Equity',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.update_layout(
            title="Portfolio Equity Over Time",
            xaxis_title="Date",
            yaxis_title="Equity ($)",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No equity curve data available")
    
    st.markdown("---")
    
    # Trades table
    st.subheader("📋 Trades")
    
    trades_df = run_manager.get_trades(run_id)
    
    if not trades_df.empty:
        st.dataframe(
            trades_df,
            use_container_width=True,
            height=400
        )
        
        # Download button
        csv = trades_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Trades CSV",
            data=csv,
            file_name=f"trades_{run_id}.csv",
            mime="text/csv"
        )
    else:
        st.info("No trades executed in this backtest")
    
    # Cleanup
    run_manager.close()
