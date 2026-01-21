# Cross-Currency Payment Service (Python / FastAPI)

A complete backend service that processes cross-currency payments using an external FX rate provider. Built in Python (FastAPI). The service accepts a payment request, retrieves an FX quote, computes a payout, persists the payment, and returns detailed diagnostics.

# Layer Breakdown
## models.py

Defines domain objects (Payment, PaymentStatus)

Handles API validation and serialization

Ensures values like amount > 0 and currencies are non-empty

## repository.py

Simple, thread-safe in-memory data store

Stores PaymentRecord dataclasses

Converts back to Pydantic models on retrieval

## fx_client.py

Async HTTP client using httpx

Calls Ripple’s Twirp FX service

Handles:

Timeouts

Retries

Response validation

Latency measurement

## routers.py

Implements the /payments API endpoints

Manages PENDING → SUCCEEDED/FAILED transitions

Persists and retrieves payments

Saves FX diagnostics on failure

## main.py

Application entrypoint

Creates global repo and fx_client

Registers the router and CORS middleware

Exposes /health endpoint.

# API Endpoints
## POST /payments

Create and process a new cross-currency payment.

Request
{
  "sender": "Alice",
  "receiver": "Bob",
  "amount": 100,
  "source_currency": "USD",
  "destination_currency": "EUR"
}

Success Response — 201
{
  "id": "f8c0...",
  "sender": "Alice",
  "receiver": "Bob",
  "amount": 100,
  "source_currency": "USD",
  "destination_currency": "EUR",
  "status": "SUCCEEDED",
  "payout_amount": 92.13,
  "fx_rate": 0.9213,
  "diagnostics": { "fx_latency_ms": 243 },
  "payout_currency": "EUR"
}

Failure Response — 502 (FX error)
{
  "detail": "Failed to obtain FX rate"
}

## GET /payments/{id}

Retrieve an existing payment.

Example Response
{
  "id": "f8c0...",
  "status": "FAILED",
  "error_message": "FX service returned status 500",
  "diagnostics": {
    "fx_error": "FX service returned status 500"
  }
}

# Get Started

1. Install dependencies

pip install -r requirements.txt

2. Start Ripple’s FX service

(from the provided exercise repo)

npm install
npm start

Runs at: http://localhost:4000

3. Run the Python service

uvicorn app.main:app --reload --port 8080

# Ai Tool implementation

Generated and refined scaffolding (FastAPI routes, Pydantic models, retry logic).

Used AI to brainstorm architecture, failure modes, edge cases.