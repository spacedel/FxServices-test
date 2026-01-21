# app/main.py

# --------------------
# Application entrypoint for the FastAPI-based payment service.
# - Creates the FastAPI app.
# - Instantiates global repository and FX client.
# - Registers routes and middleware.
# - Exposes a basic health check endpoint.

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .fx_client import FXClient
from .repository import InMemoryPaymentRepository
from .routers import router as payments_router

# Global instances (used by Depends helpers in routers.py)
repo = InMemoryPaymentRepository()
fx_base_url = os.getenv("FX_BASE_URL", "http://localhost:4000")
fx_client = FXClient(base_url=fx_base_url)

app = FastAPI(
    title="Cross-Currency Payment Service",
    version="1.0.0",
)

# Optional – helpful for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(payments_router)

# Simple health check endpoint for monitoring.
@app.get("/health")
async def health():
    return {"status": "ok"}
