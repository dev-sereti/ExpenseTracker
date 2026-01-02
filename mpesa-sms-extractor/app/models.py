from __future__ import annotations
from datetime import datetime
# from decimal import Decimal
import decimal
from sqlalchemy import String, Text, DateTime, Numeric, func, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    transaction_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    transaction_date: Mapped["datetime"] = mapped_column(DateTime(timezone=True), nullable=False)

    amount: Mapped["decimal.Decimal"] = mapped_column(Numeric(12, 2), nullable=False)

    transaction_mode: Mapped[str] = mapped_column(String(16), nullable=False)  # Received/Sent/Paid/...
    sender_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    receiver_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    raw_message: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped["datetime"] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


Index("ix_transactions_date", Transaction.transaction_date)