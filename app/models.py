# app/models.py
# --------------------
# Defines the core domain and API models for the payment service:
# - Payment
# - Diagnostics
# - CreatePaymentRequest
# - PaymentStatus enum
# Uses Pydantic for validation and serialization (ID).

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# Represents the lifecycle status of a payment.
class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

# Stores diagnostic information about processing a payment, especially around the FX service call.
class Diagnostics(BaseModel):

    # How long the FX call took, in milliseconds (if available).
    fx_latency_ms: Optional[int] = Field(default=None)
    # Error message from the FX service or internal failure (if any).
    fx_error: Optional[str] = Field(default=None)

# Representation of a payment in the system.
class Payment(BaseModel):
    id: str
    sender: str
    receiver: str
    amount: float
    source_currency: str
    destination_currency: str
    status: PaymentStatus
    payout_amount: Optional[float] = None
    fx_rate: Optional[float] = None
    error_message: Optional[str] = None
    diagnostics: Diagnostics = Field(default_factory=Diagnostics)
    created_at: datetime
    updated_at: datetime
    payout_currency: str

    # Allows constructing this model from ORM-like objects if needed.
    class Config:
        from_attributes = True


# Shape of the incoming JSON body for creating a payment.
class CreatePaymentRequest(BaseModel):
    sender: str
    receiver: str
    amount: float
    source_currency: str
    destination_currency: str

    @field_validator("sender", "receiver", "source_currency", "destination_currency")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field must not be empty")
        return v

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v

# Response model for returning a payment. Currently identical to Payment. Can change if we want to hide fields later.
class PaymentResponse(Payment):
    pass
