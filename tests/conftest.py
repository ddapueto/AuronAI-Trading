"""Shared fixtures for AuronAI Trading tests."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from auronai.brokers.paper_broker import PaperBroker


@pytest.fixture
def synthetic_trades() -> list[dict]:
    """~30 trade dicts compatible with BacktestResult.trades format.

    Covers 2020-2021, ~60% win rate with realistic PnL distribution.
    Uses percentage convention: 5.0 means +5%.
    """
    rng = np.random.default_rng(42)
    n_trades = 30
    n_wins = int(n_trades * 0.6)
    n_losses = n_trades - n_wins

    win_pcts = rng.uniform(1.0, 8.0, size=n_wins)
    loss_pcts = rng.uniform(-6.0, -0.5, size=n_losses)
    pnl_pcts = np.concatenate([win_pcts, loss_pcts])
    rng.shuffle(pnl_pcts)

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    base_date = datetime(2020, 3, 1)
    trades: list[dict] = []
    for i, pnl_pct in enumerate(pnl_pcts):
        entry = base_date.replace(
            month=3 + (i * 2) // 30,
            day=1 + (i * 2) % 28,
        )
        exit_d = entry.replace(day=min(entry.day + int(rng.integers(1, 10)), 28))
        pnl_dollar = pnl_pct * 100  # Assuming ~$10k capital, $100 per 1%
        trades.append({
            "symbol": symbols[i % len(symbols)],
            "entry_date": entry.strftime("%Y-%m-%d"),
            "exit_date": exit_d.strftime("%Y-%m-%d"),
            "pnl_percent": float(pnl_pct),
            "pnl_dollar": float(pnl_dollar),
        })
    return trades


@pytest.fixture
def synthetic_equity_curve() -> pd.DataFrame:
    """Equity curve DataFrame with 'date' and 'equity' covering 2019-2022.

    Covers crisis periods needed by stress testing (COVID, Bear 2022).
    """
    dates = pd.bdate_range("2019-01-02", "2022-12-30")
    rng = np.random.default_rng(42)
    daily_returns = 0.0003 + rng.normal(0, 0.012, len(dates))
    equity = 10_000.0 * np.cumprod(1 + daily_returns)
    return pd.DataFrame({
        "date": dates.astype(str),
        "equity": equity,
    })


@pytest.fixture
def paper_broker() -> PaperBroker:
    """PaperBroker with $10,000 initial cash and no slippage/commission."""
    return PaperBroker(initial_cash=10_000.0, commission=0.0, slippage=0.0)
