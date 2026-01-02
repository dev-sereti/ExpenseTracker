from __future__ import annotations

from datetime import date, datetime, time
from typing import Iterable

from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Transaction
from app.schemas import ParsedTransaction


def create_transaction(db: Session, parsed: ParsedTransaction, raw_message: str) -> tuple[bool, Transaction]:
    tx = Transaction(
        transaction_code=parsed.transaction_code,
        transaction_date=parsed.transaction_date,
        amount=parsed.amount,
        transaction_mode=parsed.transaction_mode,
        sender_name=parsed.sender_name,
        receiver_name=parsed.receiver_name,
        raw_message=raw_message,
    )

    db.add(tx)
    try:
        db.commit()
        db.refresh(tx)
        return True, tx
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Transaction).where(Transaction.transaction_code == parsed.transaction_code)
        )
        # existing should exist because unique constraint failed, but be defensive:
        if existing:
            return False, existing
        raise


def list_transactions(
    db: Session,
    q: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> list[Transaction]:
    stmt = select(Transaction)

    if q:
        stmt = stmt.where(Transaction.transaction_code.ilike(f"%{q.strip()}%"))

    if start:
        start_dt = datetime.combine(start, time.min).astimezone(Transaction.transaction_date.type.timezone)  # type: ignore
        # the above isn't reliable across dialects; do a simpler tz-aware combine below:
        start_dt = datetime(start.year, start.month, start.day, 0, 0, 0, tzinfo=None)
        stmt = stmt.where(Transaction.transaction_date >= start_dt)

    if end:
        end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=None)
        stmt = stmt.where(Transaction.transaction_date <= end_dt)

    stmt = stmt.order_by(desc(Transaction.transaction_date), desc(Transaction.created_at))
    return list(db.scalars(stmt).all())


def get_all_transactions(db: Session) -> list[Transaction]:
    stmt = select(Transaction).order_by(desc(Transaction.transaction_date), desc(Transaction.created_at))
    return list(db.scalars(stmt).all())