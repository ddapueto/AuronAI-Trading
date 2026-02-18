"""
Main Streamlit application for Swing Strategy Lab.

This is the entry point for the interactive UI that allows users to:
- Configure and run backtests
- Visualize results
- Compare multiple strategies

**Validates: Requirements FR-15, FR-16, FR-17**
"""

import streamlit as st
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Swing Strategy Lab",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main application entry point."""
    
    # Sidebar navigation
    st.sidebar.title("📈 Swing Strategy Lab")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🚀 Run Backtest", "🔄 Walk-Forward", "📊 View Results", "🔍 Compare Runs"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### About
    
    Swing Strategy Lab is a visual laboratory for quantitative strategy development.
    
    **Features:**
    - Multiple strategy types (Long, Short, Neutral)
    - Regime detection (Bull/Bear/Neutral)
    - Walk-forward optimization
    - Comprehensive metrics
    - Run comparison
    """)
    
    # Route to appropriate page
    if page == "🚀 Run Backtest":
        from auronai.ui.pages import run_backtest
        run_backtest.show()
    elif page == "🔄 Walk-Forward":
        from auronai.ui.pages import walk_forward
        walk_forward.show()
    elif page == "📊 View Results":
        from auronai.ui.pages import view_results
        view_results.show()
    elif page == "🔍 Compare Runs":
        from auronai.ui.pages import compare_runs
        compare_runs.show()


if __name__ == "__main__":
    main()
