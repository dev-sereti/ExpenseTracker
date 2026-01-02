from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ParsedTransaction(BaseModel):
    transaction_code: str = Field(..., min_length=6, max_length=32)
    transaction_date: datetime
    amount: Decimal
    transaction_mode: str

    sender_name: str | None = None
    receiver_name: str | None = None


class TransactionOut(BaseModel):
    id: int
    transaction_code: str
    transaction_date: datetime
    amount: Decimal
    transaction_mode: str
    sender_name: str | None
    receiver_name: str | None
    raw_message: str
    created_at: datetime

    class Config:
        from_attributes = True