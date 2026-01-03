from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import Transaction

TZ_NAIROBI = ZoneInfo("Africa/Nairobi")
DASH_MODES = ("Sent", "Received", "Paid")


def _month_add(year: int, month: int, delta_months: int) -> tuple[int, int]:
    # month in 1..12
    total = (year * 12 + (month - 1)) + delta_months
    new_year = total // 12
    new_month = (total % 12) + 1
    return new_year, new_month


def _month_start(dt: datetime) -> datetime:
    # tz-aware month start in Nairobi
    dt_n = dt.astimezone(TZ_NAIROBI) if dt.tzinfo else dt.replace(tzinfo=TZ_NAIROBI)
    return datetime(dt_n.year, dt_n.month, 1, 0, 0, 0, tzinfo=TZ_NAIROBI)


def _decimal_to_float_2(x: Decimal) -> float:
    # keep 2dp display behavior (Excel/Chart friendly)
    return float(x.quantize(Decimal("0.01")))


@dataclass(frozen=True)
class DashboardData:
    months: list[str]                       # ["2025-11", "2025-12", "2026-01"]
    monthly: dict[str, list[float]]         # {"Sent":[..], "Received":[..], "Paid":[..], "Net":[..]}
    cumulative: dict[str, list[float]]      # running totals over months
    totals: dict[str, float]                # totals over last 3 months
    window_start: datetime
    window_end: datetime


def build_dashboard_data(db: Session, now: datetime | None = None) -> DashboardData:
    now = now or datetime.now(tz=TZ_NAIROBI)
    now = now.astimezone(TZ_NAIROBI)

    # Build the last 3 months (including current month): [M-2, M-1, M]
    cur_start = _month_start(now)
    y2, m2 = _month_add(cur_start.year, cur_start.month, -2)
    oldest_start = datetime(y2, m2, 1, 0, 0, 0, tzinfo=TZ_NAIROBI)

    month_starts: list[datetime] = [
        oldest_start,
        datetime(*_month_add(oldest_start.year, oldest_start.month, 1), 1, 0, 0, 0, tzinfo=TZ_NAIROBI),
        datetime(*_month_add(oldest_start.year, oldest_start.month, 2), 1, 0, 0, 0, tzinfo=TZ_NAIROBI),
    ]
    months = [ms.strftime("%Y-%m") for ms in month_starts]

    # Query monthly sums per mode for the window
    month_expr = func.date_trunc("month", Transaction.transaction_date).label("month")

    stmt = (
        select(
            month_expr,
            Transaction.transaction_mode.label("mode"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .where(Transaction.transaction_date >= oldest_start)
        .where(Transaction.transaction_mode.in_(DASH_MODES))
        .group_by(month_expr, Transaction.transaction_mode)
        .order_by(month_expr.asc())
    )

    rows = db.execute(stmt).all()

    # Initialize zeroed series
    monthly_dec: dict[str, list[Decimal]] = {mode: [Decimal("0.00")] * 3 for mode in DASH_MODES}

    # Fill from query results
    month_index = {label: i for i, label in enumerate(months)}
    for month_dt, mode, total in rows:
        # month_dt can be tz-aware depending on driver; normalize to label
        label = month_dt.astimezone(TZ_NAIROBI).strftime("%Y-%m") if getattr(month_dt, "tzinfo", None) else month_dt.strftime("%Y-%m")
        idx = month_index.get(label)
        if idx is not None and mode in monthly_dec:
            monthly_dec[mode][idx] = Decimal(total)

    # Compute monthly net: Received - (Sent + Paid)
    monthly_dec["Net"] = [
        (monthly_dec["Received"][i] - (monthly_dec["Sent"][i] + monthly_dec["Paid"][i])).quantize(Decimal("0.01"))
        for i in range(3)
    ]

    # Cumulative running totals across months
    cumulative_dec: dict[str, list[Decimal]] = {}
    for key, series in monthly_dec.items():
        run = Decimal("0.00")
        out: list[Decimal] = []
        for v in series:
            run += v
            out.append(run.quantize(Decimal("0.01")))
        cumulative_dec[key] = out

    # Totals over the 3 months
    totals_dec = {k: sum(v, Decimal("0.00")).quantize(Decimal("0.01")) for k, v in monthly_dec.items()}

    return DashboardData(
        months=months,
        monthly={k: [_decimal_to_float_2(x) for x in v] for k, v in monthly_dec.items()},
        cumulative={k: [_decimal_to_float_2(x) for x in v] for k, v in cumulative_dec.items()},
        totals={k: _decimal_to_float_2(v) for k, v in totals_dec.items()},
        window_start=oldest_start,
        window_end=now,
    )