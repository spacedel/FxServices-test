# app/repository.py
# app/repository.py
# --------------------
# Provides a simple in-memory repository for storing payments.
# This is intentionally lightweight, but the interface could later be backed by a real database.

from __future__ import annotations

from dataclasses import dataclass, asdict
from threading import RLock
from typing import Dict

from .models import Payment

# Raised when a payment cannot be found in the repository.
class PaymentNotFound(Exception):
    pass

# Dataclass representation of a Payment used for internal storage.
# We store primitive types here (like dict for diagnostics) instead of nested Pydantic models to keep the storage layer decoupled from the API modeling library.
@dataclass
class PaymentRecord:
    # A simple dataclass representation of Payment for storage
    id: str
    sender: str
    receiver: str
    amount: float
    source_currency: str
    destination_currency: str
    status: str
    payout_amount: float | None
    fx_rate: float | None
    error_message: str | None
    diagnostics: dict
    created_at: str
    updated_at: str
    payout_currency: str

# Thread-safe in-memory implementation of a payment repository. For a real system, this would likely be replaced with a DB-backed repository.
class InMemoryPaymentRepository:
    
    def __init__(self) -> None:
        # Re-entrant lock to guard the internal map.
        self._lock = RLock()
        # Maps payment ID → PaymentRecord
        self._payments: Dict[str, PaymentRecord] = {}

    # Insert a new payment record. If the ID already exists, it will be overwritten (not ideal for a real system).
    def save(self, payment: Payment) -> None:
        # Convert Pydantic Payment model into a PaymentRecord dataclass.
        rec = PaymentRecord(**payment.model_dump())
        with self._lock:
            self._payments[payment.id] = rec

    # Update an existing payment record. Raises: PaymentNotFound: if the payment ID is not known.
    def update(self, payment: Payment) -> None:
        with self._lock:
            if payment.id not in self._payments:
                raise PaymentNotFound(payment.id)
            self._payments[payment.id] = PaymentRecord(**payment.model_dump())
    
    # Retrieve a payment by its ID.
    def get(self, payment_id: str) -> Payment:
        with self._lock:
            rec = self._payments.get(payment_id)
            if not rec:
                raise PaymentNotFound(payment_id)

        # Convert back to Payment
        return Payment(**asdict(rec))
