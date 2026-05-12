"""FastAPI entrypoint for PeD Power Solis."""

from __future__ import annotations

from fastapi import FastAPI

from api.routes import router as api_router


app = FastAPI(
    title="PeD Power Solis API",
    version="0.1.0",
    description="HTTP API for TC diagnostic inference.",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""

    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Basic service metadata."""

    return {
        "service": "PeD Power Solis API",
        "health": "/health",
        "docs": "/docs",
    }


app.include_router(api_router, prefix="/api/v1", tags=["diagnostics"])
