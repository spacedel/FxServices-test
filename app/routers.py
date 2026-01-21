# app/routers.py
# --------------------
# Defines the HTTP routes for interacting with payments:
# - POST /payments: create and process a new payment.
# - GET /payments/{payment_id}: retrieve an existing payment.
#
# Uses FastAPI's dependency injection to access the repository and FX client.

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from .fx_client import FXClient
from .models import CreatePaymentRequest, Payment, PaymentResponse, PaymentStatus, Diagnostics
from .repository import InMemoryPaymentRepository, PaymentNotFound

router = APIRouter(prefix="/payments", tags=["payments"])


# Simple dependency injection helpers
def get_repo() -> InMemoryPaymentRepository:
    from .main import repo  # circular-safe import

    return repo


def get_fx_client() -> FXClient:
    from .main import fx_client  # circular-safe import

    return fx_client


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)

# Create and process a new payment.
#    Steps:
#    1. Build a Payment object in PENDING state.
#    2. Persist it.
#    3. Call the FX service to get the rate.
#    4. On success, update the payment with payout and SUCCEEDED status.
#    5. On failure, mark it as FAILED and store diagnostics, then return 502.

async def create_payment(
    req: CreatePaymentRequest,
    repo: InMemoryPaymentRepository = Depends(get_repo),
    fx_client: FXClient = Depends(get_fx_client),
) -> PaymentResponse:
    now = datetime.now(timezone.utc)

    # Initialize payment in PENDING state.
    payment = Payment(
        id=str(uuid4()),
        sender=req.sender.strip(),
        receiver=req.receiver.strip(),
        amount=req.amount,
        source_currency=req.source_currency.strip().upper(),
        destination_currency=req.destination_currency.strip().upper(),
        status=PaymentStatus.PENDING,
        payout_amount=None,
        fx_rate=None,
        error_message=None,
        diagnostics=Diagnostics(),
        created_at=now,
        updated_at=now,
        payout_currency=req.destination_currency.strip().upper(),
    )

    # Save initial PENDING state
    repo.save(payment)

    # Call FX service with a timeout / retries inside the client
    try:
        rate, latency_ms = await fx_client.get_quote(
            payment.source_currency, payment.destination_currency
        )
        payment.diagnostics.fx_latency_ms = latency_ms
        payment.fx_rate = rate
        payout = payment.amount * rate
        payment.payout_amount = payout
        payment.status = PaymentStatus.SUCCEEDED
        payment.updated_at = datetime.now(timezone.utc)
        repo.update(payment)
    except Exception as exc:
        msg = str(exc)
        payment.diagnostics.fx_error = msg
        payment.error_message = msg
        payment.status = PaymentStatus.FAILED
        payment.updated_at = datetime.now(timezone.utc)
        repo.update(payment)
        # Upstream failure → Bad Gateway
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to obtain FX rate",
        )

    return PaymentResponse(**payment.model_dump())


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment(
    payment_id: str,
    repo: InMemoryPaymentRepository = Depends(get_repo),
) -> PaymentResponse:
    try:
        payment = repo.get(payment_id)
    except PaymentNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return PaymentResponse(**payment.model_dump())
