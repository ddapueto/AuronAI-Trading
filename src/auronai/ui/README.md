# Swing Strategy Lab - Streamlit UI

Interactive web interface for quantitative strategy development and backtesting.

## Features

### 🚀 Run Backtest
- Configure strategy parameters (Long/Short/Neutral)
- Select trading universe and date range
- Execute backtests with real-time progress
- View immediate results

### 📊 View Results
- Comprehensive performance metrics
- Interactive equity curve charts
- Detailed trades table
- Export results to CSV

### 🔍 Compare Runs
- Side-by-side comparison of multiple runs
- Overlay equity curves
- Metrics comparison table
- Visual performance analysis

## Quick Start

### Launch the App

```bash
# From project root
./scripts/run_streamlit_app.sh

# Or manually
streamlit run src/auronai/ui/app.py
```

The app will open in your browser at `http://localhost:8501`

### First Time Setup

1. The app will use the existing `data/cache` and `data/runs.db`
2. If no data exists, run a backtest to generate demo data
3. Results are automatically saved and can be compared

## Usage Guide

### Running a Backtest

1. Go to "🚀 Run Backtest" page
2. Select strategy type:
   - **Long Momentum**: Buys top performers in bull markets
   - **Short Momentum**: Shorts weak performers in bear markets
   - **Neutral**: Defensive positions in neutral markets
3. Configure parameters:
   - **Top K**: Number of symbols to trade (1-10)
   - **Holding Period**: Days to hold positions (1-30)
4. Set date range and trading universe
5. Click "▶️ Run Backtest"

### Viewing Results

1. After running a backtest, go to "📊 View Results"
2. Review key metrics:
   - Total Return, CAGR, Sharpe Ratio
   - Max Drawdown, Win Rate
3. Analyze equity curve
4. Review individual trades
5. Download trades as CSV

### Comparing Runs

1. Go to "🔍 Compare Runs"
2. Select 2-4 runs from the dropdown
3. Compare metrics side-by-side
4. View overlaid equity curves
5. Identify best performing strategies

## Architecture

```
src/auronai/ui/
├── app.py              # Main entry point
├── pages/
│   ├── run_backtest.py    # Backtest configuration and execution
│   ├── view_results.py    # Results visualization
│   └── compare_runs.py    # Multi-run comparison
└── README.md           # This file
```

## Dependencies

- `streamlit>=1.28.0` - Web framework
- `plotly>=5.17.0` - Interactive charts
- `pandas>=2.0.0` - Data manipulation

## Configuration

The app uses the following defaults:

- **Cache Directory**: `data/cache/`
- **Database**: `data/runs.db`
- **Port**: 8501
- **Theme**: Light mode with blue primary color

## Tips

- Run backtests with different parameters to find optimal settings
- Compare strategies across different market conditions
- Use the benchmark (SPY/QQQ) to evaluate relative performance
- Export trades for further analysis in Excel/Python

## Troubleshooting

### App won't start
- Ensure Streamlit is installed: `pip install streamlit plotly`
- Check port 8501 is not in use

### No data showing
- Run a backtest first to generate data
- Check `data/runs.db` exists

### Slow performance
- Reduce date range for faster backtests
- Limit number of symbols in trading universe
- Use cached data when available

## Future Enhancements

- [ ] Real-time progress updates during backtest
- [ ] Advanced filtering and sorting of runs
- [ ] Regime breakdown visualization
- [ ] Parameter optimization interface
- [ ] Export to PDF reports
