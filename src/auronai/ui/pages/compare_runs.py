"""
Compare Runs page.

Allows users to compare metrics and performance across multiple backtest runs.

**Validates: Requirements FR-17, FR-14**
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from auronai.backtesting import RunManager


def show():
    """Display the Compare Runs page."""
    
    try:
        st.title("🔍 Compare Runs")
        st.markdown("Compare performance across multiple backtest runs.")
        st.markdown("---")
        
        # Load available runs
        run_manager = RunManager(db_path="data/runs.db")
        all_runs = run_manager.list_runs(limit=50)
        
        if not all_runs:
            st.warning("No backtest runs available. Please run a backtest first.")
            run_manager.close()
            return
        
        # Create run selector
        run_options = {
            f"{run.strategy_id} - {run.created_at.strftime('%Y-%m-%d %H:%M')} ({run.run_id[:8]})": run.run_id
            for run in all_runs
        }
        
        selected_labels = st.multiselect(
            "Select runs to compare (2-4 recommended)",
            options=list(run_options.keys()),
            default=list(run_options.keys())[:min(3, len(run_options))],
            help="Select 2-4 runs for meaningful comparison"
        )
        
        if not selected_labels:
            st.info("Please select at least one run to display")
            run_manager.close()
            return
        
        selected_run_ids = [run_options[label] for label in selected_labels]
        
        # Get comparison data
        comparison_df = run_manager.compare_runs(selected_run_ids)
        
        if comparison_df.empty:
            st.error("Could not load comparison data")
            run_manager.close()
            return
        
        # Display metrics comparison
        st.subheader("📊 Metrics Comparison")
        
        # Create tabs for different metric categories
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Returns", 
            "⚠️ Risk", 
            "🎯 Risk-Adjusted", 
            "💼 Trading"
        ])
        
        with tab1:
            st.markdown("### Return Metrics")
            return_metrics = ['strategy', 'total_return', 'cagr', 'final_equity']
            if all(col in comparison_df.columns for col in return_metrics):
                display_df = comparison_df[return_metrics].copy()
                
                # Format percentages
                for col in ['total_return', 'cagr']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}")
                
                # Format currency
                if 'final_equity' in display_df.columns:
                    display_df[col] = display_df['final_equity'].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Some return metrics are not available")
        
        with tab2:
            st.markdown("### Risk Metrics")
            risk_metrics = [
                'strategy', 'max_drawdown', 'volatility', 
                'avg_dd_duration', 'max_dd_duration', 'ulcer_index'
            ]
            available_risk_metrics = ['strategy'] + [m for m in risk_metrics[1:] if m in comparison_df.columns]
            
            if len(available_risk_metrics) > 1:
                display_df = comparison_df[available_risk_metrics].copy()
                
                # Format percentages
                for col in ['max_drawdown', 'volatility']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}")
                
                # Format numbers
                for col in ['avg_dd_duration', 'max_dd_duration', 'ulcer_index']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Risk metrics are not available")
        
        with tab3:
            st.markdown("### Risk-Adjusted Metrics")
            risk_adj_metrics = [
                'strategy', 'sharpe_ratio', 'sortino_ratio', 
                'calmar_ratio', 'recovery_factor'
            ]
            available_risk_adj = ['strategy'] + [m for m in risk_adj_metrics[1:] if m in comparison_df.columns]
            
            if len(available_risk_adj) > 1:
                display_df = comparison_df[available_risk_adj].copy()
                
                # Format numbers
                for col in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'recovery_factor']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Add interpretation guide
                st.markdown("""
                **Interpretation Guide:**
                - **Sharpe/Sortino >1.5**: Excellent
                - **Calmar >2.0**: Very good
                - **Recovery Factor >3.0**: Strong resilience
                """)
            else:
                st.warning("Risk-adjusted metrics are not available")
        
        with tab4:
            st.markdown("### Trading Metrics")
            trading_metrics = [
                'strategy', 'num_trades', 'win_rate', 'profit_factor', 
                'expectancy', 'max_consecutive_losses'
            ]
            available_trading = ['strategy'] + [m for m in trading_metrics[1:] if m in comparison_df.columns]
            
            if len(available_trading) > 1:
                display_df = comparison_df[available_trading].copy()
                
                # Format percentages
                if 'win_rate' in display_df.columns:
                    display_df['win_rate'] = display_df['win_rate'].apply(lambda x: f"{x:.2%}")
                
                # Format numbers
                for col in ['profit_factor', 'expectancy']:
                    if col in display_df.columns:
                        if col == 'expectancy':
                            display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}")
                        else:
                            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Trading metrics are not available")
        
        st.markdown("---")
        
        # Equity curves comparison
        st.subheader("💰 Equity Curves Comparison")
        
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for i, run_id in enumerate(selected_run_ids):
            equity_df = run_manager.get_equity_curve(run_id)
            
            if not equity_df.empty:
                run = run_manager.get_run(run_id)
                label = f"{run.strategy_id} ({run_id[:8]})"
                
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(equity_df['date']),
                    y=equity_df['equity'],
                    mode='lines',
                    name=label,
                    line=dict(color=colors[i % len(colors)], width=2)
                ))
        
        fig.update_layout(
            title="Portfolio Equity Comparison",
            xaxis_title="Date",
            yaxis_title="Equity ($)",
            hovermode='x unified',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Returns comparison bar chart
        st.subheader("📈 Returns Comparison")
        
        fig_returns = go.Figure()
        
        fig_returns.add_trace(go.Bar(
            x=comparison_df['strategy'],
            y=comparison_df['total_return'] * 100,
            text=comparison_df['total_return'].apply(lambda x: f"{x:.2%}"),
            textposition='auto',
            marker_color=colors[:len(comparison_df)]
        ))
        
        fig_returns.update_layout(
            title="Total Return Comparison",
            xaxis_title="Strategy",
            yaxis_title="Return (%)",
            height=400
        )
        
        st.plotly_chart(fig_returns, use_container_width=True)
        
        # Cleanup
        run_manager.close()
        
    except Exception as e:
        st.error(f"❌ Error loading comparison: {str(e)}")
        st.exception(e)
        try:
            run_manager.close()
        except:
            pass
