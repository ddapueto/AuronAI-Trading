"""Tests for AuronAI Trading API endpoints."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from auronai.api.main import app
from auronai.brokers.models import OrderSide, OrderStatus

# ── Health ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_no_auth(client):
    """Health endpoint should work without API key."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["broker"] == "paper"


# ── Auth ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_auth_required_when_keys_configured(mock_broker):
    """Endpoints should return 401 when API keys are set but none provided."""
    from auronai.api import dependencies as deps
    from auronai.api import middleware

    middleware._VALID_KEYS = None
    os.environ["AURONAI_API_KEYS"] = "secret-key-123"

    async def _get_broker():
        return mock_broker

    app.dependency_overrides[deps.get_broker] = _get_broker

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/trading/account")
            assert resp.status_code == 401

            # With correct key → 200
            resp = await ac.get(
                "/api/trading/account",
                headers={"X-API-Key": "secret-key-123"},
            )
            assert resp.status_code == 200
    finally:
        os.environ.pop("AURONAI_API_KEYS", None)
        app.dependency_overrides.clear()
        middleware._VALID_KEYS = None


@pytest.mark.asyncio
async def test_health_bypasses_auth(mock_broker):
    """Health should work even when API keys are configured."""
    from auronai.api import dependencies as deps
    from auronai.api import middleware

    middleware._VALID_KEYS = None
    os.environ["AURONAI_API_KEYS"] = "secret-key-123"

    async def _get_broker():
        return mock_broker

    app.dependency_overrides[deps.get_broker] = _get_broker

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/health")
            assert resp.status_code == 200
    finally:
        os.environ.pop("AURONAI_API_KEYS", None)
        app.dependency_overrides.clear()
        middleware._VALID_KEYS = None


# ── Account ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_account(client):
    resp = await client.get("/api/trading/account")
    assert resp.status_code == 200
    data = resp.json()
    assert data["broker"] == "paper"
    assert data["cash"] == 10_000.0
    assert data["is_paper"] is True


# ── Positions ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_positions_empty(client):
    resp = await client.get("/api/trading/positions")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_positions_with_data(client, mock_broker):
    from tests.api.conftest import _make_position

    mock_broker.get_positions.return_value = [
        _make_position("AAPL", 10, 150.0, 155.0),
    ]
    resp = await client.get("/api/trading/positions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["unrealized_pnl"] == 50.0


# ── Kill Switch ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_kill_switch_no_positions(client):
    resp = await client.post("/api/trading/kill-switch")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cancelled_orders"] == 0
    assert data["closed_positions"] == 0


@pytest.mark.asyncio
async def test_kill_switch_with_positions(client, mock_broker):
    from tests.api.conftest import _make_order, _make_position

    mock_broker.get_positions.return_value = [
        _make_position("AAPL"),
        _make_position("MSFT", qty=5, entry=300.0, current=310.0),
    ]
    mock_broker.close_position.return_value = _make_order()

    resp = await client.post("/api/trading/kill-switch")
    assert resp.status_code == 200
    data = resp.json()
    assert data["closed_positions"] == 2
    assert len(data["details"]) == 2


# ── Signals ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_signals(client):
    resp = await client.get("/api/signals/")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "buy_signals" in data
    assert "sell_signals" in data
    assert "results" in data


# ── Metrics ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_metrics(client):
    resp = await client.get("/api/metrics/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["equity"] == 10_000.0
    assert data["cash"] == 10_000.0
    assert data["unrealized_pnl"] == 0.0
    assert data["total_trades"] == 0


@pytest.mark.asyncio
async def test_get_metrics_with_positions(client, mock_broker):
    from tests.api.conftest import _make_account, _make_order, _make_position

    pos = _make_position("AAPL", 10, 150.0, 155.0)
    mock_broker.get_positions.return_value = [pos]
    # Update account to reflect position
    acc = _make_account(cash=8500.0)
    acc.equity = 8500.0 + pos.market_value
    mock_broker.get_account.return_value = acc

    # Add a filled order
    order = _make_order("AAPL", OrderSide.BUY, 10, OrderStatus.FILLED, 150.0)
    mock_broker._orders = {"test-001": order}

    resp = await client.get("/api/metrics/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unrealized_pnl"] == 50.0
    assert data["total_trades"] == 1
    assert data["exposure"] > 0


# ── Trade History ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trade_history_empty(client):
    resp = await client.get("/api/trading/trade-history")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_trade_history_with_orders(client, mock_broker):
    from tests.api.conftest import _make_order

    order = _make_order("AAPL", OrderSide.BUY, 10, OrderStatus.FILLED, 150.0)
    mock_broker._orders = {"test-001": order}

    resp = await client.get("/api/trading/trade-history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["status"] == "filled"


# ── Risk ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_position_size(client):
    resp = await client.post(
        "/api/risk/position-size",
        json={
            "entry_price": 150.0,
            "stop_loss": 145.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "shares" in data
    assert "risk_amount" in data
