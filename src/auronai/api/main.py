"""FastAPI application — AuronAI Trading API."""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from auronai.api.dependencies import get_broker
from auronai.api.middleware import limiter, verify_api_key
from auronai.api.routers import (
    analysis,
    backtest,
    market,
    metrics,
    risk,
    scanner,
    signals,
    trading,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize singletons on startup, clean up on shutdown."""
    logger.info("Starting AuronAI Trading API …")
    broker = await get_broker()
    logger.info("PaperBroker ready (cash=%.2f)", (await broker.get_account()).cash)
    yield
    await broker.disconnect()
    logger.info("AuronAI Trading API shut down.")


app = FastAPI(
    title="AuronAI Trading API",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Rate limiting ────────────────────────────────────────────────────────

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."},
    )


# ── CORS ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health (no auth) ─────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    """Health check endpoint (no auth required)."""
    broker = await get_broker()
    return {
        "status": "ok",
        "broker": broker.name,
        "connected": broker.is_connected,
    }


# ── Authenticated routers ───────────────────────────────────────────────

auth_router = APIRouter(dependencies=[Depends(verify_api_key)])
auth_router.include_router(market.router)
auth_router.include_router(analysis.router)
auth_router.include_router(scanner.router)
auth_router.include_router(trading.router)
auth_router.include_router(risk.router)
auth_router.include_router(backtest.router)
auth_router.include_router(signals.router)
auth_router.include_router(metrics.router)

app.include_router(auth_router)
