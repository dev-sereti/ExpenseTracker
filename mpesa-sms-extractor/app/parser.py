from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from app.schemas import ParsedTransaction


TZ_NAIROBI = ZoneInfo("Africa/Nairobi")


class ParseError(ValueError):
    pass


_AMOUNT_RE = re.compile(
    r"\bKsh\s*([0-9][0-9,]*)(?:\.(\d{1,2}))?\b",
    flags=re.IGNORECASE,
)

_CODE_RE = re.compile(r"^\s*([A-Z0-9]{6,32})\b")

_DATETIME_RE = re.compile(
    r"\bon\s+(\d{1,2})/(\d{1,2})/(\d{2,4})"
    r"(?:\s+at\s+(\d{1,2}):(\d{2})(?:\s*([AP]M))?)?",
    flags=re.IGNORECASE,
)

# Name capture: stop before phone number or " on " / "." / " at "
_NAME_STOP_RE = r"(?:\s+\d{9,}|\s+on\b|\s+at\b|[.])"


def _normalize_text(text: str) -> str:
    # Keep original for raw_message; this is for parsing.
    text = text.replace("\r\n", "\n").strip()
    # Make spacing more predictable
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _parse_amount(text: str) -> Decimal:
    m = _AMOUNT_RE.search(text)
    if not m:
        raise ParseError("Could not find an amount (expected something like 'Ksh1,000.00').")

    whole = m.group(1).replace(",", "")
    frac = m.group(2) or "00"
    try:
        amt = Decimal(f"{whole}.{frac}")
    except InvalidOperation as e:
        raise ParseError("Amount was present but could not be parsed.") from e

    # Normalize to 2dp
    return amt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parse_datetime(text: str) -> datetime:
    m = _DATETIME_RE.search(text)
    if not m:
        raise ParseError("Could not find a transaction date/time (expected 'on d/m/yy at h:mm AM/PM').")

    day_s, month_s, year_s, hh_s, mm_s, ampm = m.groups()
    day = int(day_s)
    month = int(month_s)
    year = int(year_s)
    if year < 100:
        year += 2000

    hour = int(hh_s) if hh_s else 0
    minute = int(mm_s) if mm_s else 0

    if ampm:
        ampm_u = ampm.upper()
        if ampm_u == "PM" and hour != 12:
            hour += 12
        if ampm_u == "AM" and hour == 12:
            hour = 0

    try:
        dt = datetime(year, month, day, hour, minute, tzinfo=TZ_NAIROBI)
    except ValueError as e:
        raise ParseError("Found a date/time but it was invalid.") from e

    return dt


def _clean_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s{2,}", " ", name)
    name = name.strip(" .")
    return name or None  # type: ignore[return-value]


def _detect_mode(text: str) -> str:
    t = text.lower()

    # Order matters: more specific first.
    if " sent to " in f" {t} ":
        return "Sent"
    if " you have received " in f" {t} " or (" received " in f" {t} " and " from " in f" {t} "):
        return "Received"
    if " paid to " in f" {t} ":
        return "Paid"
    if "withdraw" in t:
        return "Withdraw"
    if "deposit" in t:
        return "Deposit"
    if "reversal" in t or "reversed" in t:
        return "Reversal"
    return "Other"


def _extract_party(text: str, mode: str) -> tuple[str | None, str | None]:
    sender = None
    receiver = None

    if mode == "Sent":
        m = re.search(r"\bsent to\s+(.+?)" + _NAME_STOP_RE, text, flags=re.IGNORECASE)
        if m:
            receiver = _clean_name(m.group(1))
    elif mode == "Received":
        m = re.search(r"\bfrom\s+(.+?)" + _NAME_STOP_RE, text, flags=re.IGNORECASE)
        if m:
            sender = _clean_name(m.group(1))
    elif mode == "Paid":
        m = re.search(r"\bpaid to\s+(.+?)" + _NAME_STOP_RE, text, flags=re.IGNORECASE)
        if m:
            receiver = _clean_name(m.group(1))

    return sender, receiver


def parse_mpesa_message(text: str) -> ParsedTransaction:
    if not text or not text.strip():
        raise ParseError("Please paste an M-PESA message.")

    norm = _normalize_text(text)

    code_m = _CODE_RE.search(norm)
    if not code_m:
        raise ParseError("Could not find a transaction code at the start of the message.")
    transaction_code = code_m.group(1).strip()

    amount = _parse_amount(norm)
    transaction_date = _parse_datetime(norm)
    mode = _detect_mode(norm)
    sender, receiver = _extract_party(norm, mode)

    # Critical field validation per requirements
    if not transaction_code or amount is None or transaction_date is None:
        raise ParseError("Missing required fields (transaction code, amount, or date).")

    return ParsedTransaction(
        transaction_code=transaction_code,
        transaction_date=transaction_date,
        amount=amount,
        transaction_mode=mode,
        sender_name=sender,
        receiver_name=receiver,
    )