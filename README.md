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

Exposes /health endpoint