"""
Run Backtest page.

Allows users to configure and execute backtests with different strategies.

**Validates: Requirements FR-15**
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from auronai.backtesting import BacktestRunner, BacktestConfig, RunManager
from auronai.data.parquet_cache import ParquetCache
from auronai.data.feature_store import FeatureStore
from auronai.strategies import (
    LongMomentumStrategy,
    ShortMomentumStrategy,
    NeutralStrategy,
    StrategyParams,
    RegimeEngine
)
from auronai.strategies.swing_tp import SwingTPStrategy


def show():
    """Display the Run Backtest page."""
    
    st.title("🚀 Run Backtest")
    st.markdown("Configure and execute a backtest with your chosen strategy.")
    st.markdown("---")
    
    # Strategy selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Strategy Configuration")
        
        strategy_type = st.selectbox(
            "Strategy Type",
            ["Long Momentum", "Short Momentum", "Neutral", "Swing TP (No SL)"],
            help="Select the trading strategy to backtest"
        )
        
        # Strategy parameters
        st.markdown("**Parameters**")
        
        top_k = st.slider(
            "Top K Symbols",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of top-ranked symbols to trade"
        )
        
        holding_days = st.slider(
            "Holding Period (days)",
            min_value=1,
            max_value=30,
            value=10,
            help="Number of days to hold positions"
        )
        
        # Date range
        st.markdown("**Date Range**")
        
        default_start = datetime.now() - timedelta(days=365)
        default_end = datetime.now()
        
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            max_value=datetime.now()
        )
        
        end_date = st.date_input(
            "End Date",
            value=default_end,
            max_value=datetime.now()
        )
        
        # Symbol selection
        st.markdown("**Symbols**")
        
        default_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 
                          'META', 'AMZN', 'NFLX', 'AMD', 'INTC']
        
        symbols_input = st.text_area(
            "Trading Universe (one per line)",
            value="\n".join(default_symbols),
            height=150,
            help="Enter stock symbols, one per line"
        )
        
        symbols = [s.strip().upper() for s in symbols_input.split('\n') if s.strip()]
        
        benchmark = st.selectbox(
            "Benchmark",
            ["SPY", "QQQ", "DIA", "IWM"],
            help="Benchmark index for comparison"
        )
        
        # Capital
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=10000.0
        )
    
    with col2:
        st.subheader("Backtest Preview")
        
        # Display configuration summary
        st.info(f"""
        **Configuration Summary**
        
        - Strategy: {strategy_type}
        - Top K: {top_k}
        - Holding Period: {holding_days} days
        - Date Range: {start_date} to {end_date}
        - Symbols: {len(symbols)} stocks
        - Benchmark: {benchmark}
        - Initial Capital: ${initial_capital:,.2f}
        """)
        
        # Validation
        errors = []
        
        if not symbols:
            errors.append("⚠️ Please enter at least one symbol")
        
        if start_date >= end_date:
            errors.append("⚠️ Start date must be before end date")
        
        if len(symbols) < top_k:
            errors.append(f"⚠️ Top K ({top_k}) cannot exceed number of symbols ({len(symbols)})")
        
        if errors:
            for error in errors:
                st.error(error)
        
        # Run button
        run_button = st.button(
            "▶️ Run Backtest",
            type="primary",
            disabled=len(errors) > 0,
            use_container_width=True
        )
        
        if run_button:
            run_backtest(
                strategy_type=strategy_type,
                top_k=top_k,
                holding_days=holding_days,
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.min.time()),
                symbols=symbols,
                benchmark=benchmark,
                initial_capital=initial_capital
            )


def run_backtest(
    strategy_type: str,
    top_k: int,
    holding_days: int,
    start_date: datetime,
    end_date: datetime,
    symbols: list,
    benchmark: str,
    initial_capital: float
):
    """Execute the backtest."""
    
    # Progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize components
        status_text.text("Initializing components...")
        progress_bar.progress(10)
        
        cache = ParquetCache(cache_dir="data/cache")
        feature_store = FeatureStore(cache_dir="data/cache")
        regime_engine = RegimeEngine(benchmark=benchmark)
        run_manager = RunManager(db_path="data/runs.db")
        
        runner = BacktestRunner(
            parquet_cache=cache,
            feature_store=feature_store,
            regime_engine=regime_engine,
            run_manager=run_manager
        )
        
        progress_bar.progress(20)
        
        # Create strategy
        status_text.text("Creating strategy...")
        
        strategy_params = StrategyParams(
            top_k=top_k,
            holding_days=holding_days
        )
        
        if strategy_type == "Long Momentum":
            strategy = LongMomentumStrategy(strategy_params)
            strategy_id = "long_momentum"
        elif strategy_type == "Short Momentum":
            strategy = ShortMomentumStrategy(strategy_params)
            strategy_id = "short_momentum"
        elif strategy_type == "Swing TP (No SL)":
            strategy = SwingTPStrategy(strategy_params)
            strategy_id = "swing_tp"
        else:
            strategy = NeutralStrategy(strategy_params)
            strategy_id = "neutral_strategy"
        
        progress_bar.progress(30)
        
        # Create config
        config = BacktestConfig(
            strategy_id=strategy_id,
            strategy_params={'top_k': top_k, 'holding_days': holding_days},
            symbols=symbols,
            benchmark=benchmark,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        # Run backtest
        status_text.text("Running backtest... This may take a minute.")
        progress_bar.progress(40)
        
        result = runner.run(config, strategy)
        
        progress_bar.progress(100)
        status_text.text("✅ Backtest complete!")
        
        # Store result in session state
        st.session_state['last_result'] = result
        st.session_state['last_run_id'] = result.run_id
        
        # Display results
        st.success(f"✅ Backtest completed successfully! Run ID: {result.run_id}")
        
        # Show key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Return",
                f"{result.metrics.get('total_return', 0):.2%}",
                delta=None
            )
        
        with col2:
            st.metric(
                "Sharpe Ratio",
                f"{result.metrics.get('sharpe_ratio', 0):.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                "Max Drawdown",
                f"{result.metrics.get('max_drawdown', 0):.2%}",
                delta=None
            )
        
        with col4:
            st.metric(
                "Trades",
                f"{result.metrics.get('num_trades', 0)}",
                delta=None
            )
        
        st.info("💡 Go to 'View Results' to see detailed analysis and charts.")
        
        # Cleanup
        run_manager.close()
        
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        st.error(f"❌ Error running backtest: {str(e)}")
        st.exception(e)
