from zoneinfo import ZoneInfo
from decimal import Decimal

import pytest

from app.parser import parse_mpesa_message, ParseError


TZ = ZoneInfo("Africa/Nairobi")


def test_parse_sent():
    msg = "QW12ABC3DE Confirmed. Ksh1,000.00 sent to JOHN DOE 07XXXXXXXX on 2/1/24 at 3:45 PM. New M-PESA balance is Ksh..."
    parsed = parse_mpesa_message(msg)
    assert parsed.transaction_code == "QW12ABC3DE"
    assert parsed.amount == Decimal("1000.00")
    assert parsed.transaction_mode == "Sent"
    assert parsed.receiver_name == "JOHN DOE"
    assert parsed.sender_name is None
    assert parsed.transaction_date.year == 2024
    assert parsed.transaction_date.month == 1
    assert parsed.transaction_date.day == 2
    assert parsed.transaction_date.hour == 15
    assert parsed.transaction_date.minute == 45
    assert parsed.transaction_date.tzinfo == TZ


def test_parse_received():
    msg = "RT98XYZ123 Confirmed. You have received Ksh500.00 from JANE DOE 07XXXXXXXX on 2/1/24 at 3:45 PM. New M-PESA balance is Ksh..."
    parsed = parse_mpesa_message(msg)
    assert parsed.transaction_code == "RT98XYZ123"
    assert parsed.amount == Decimal("500.00")
    assert parsed.transaction_mode == "Received"
    assert parsed.sender_name == "JANE DOE"
    assert parsed.receiver_name is None


def test_parse_paid():
    msg = "AB12CD34EF Confirmed. Ksh250.00 paid to ACME SUPERMARKET. on 2/1/24 at 3:45 PM. New M-PESA balance is Ksh..."
    parsed = parse_mpesa_message(msg)
    assert parsed.transaction_code == "AB12CD34EF"
    assert parsed.amount == Decimal("250.00")
    assert parsed.transaction_mode == "Paid"
    assert parsed.receiver_name == "ACME SUPERMARKET"
    assert parsed.sender_name is None


def test_parse_fails_without_code():
    msg = "Confirmed. Ksh250.00 paid to ACME SUPERMARKET. on 2/1/24 at 3:45 PM."
    with pytest.raises(ParseError):
        parse_mpesa_message(msg)


def test_parse_fails_without_amount():
    msg = "AB12CD34EF Confirmed. paid to ACME SUPERMARKET. on 2/1/24 at 3:45 PM."
    with pytest.raises(ParseError):
        parse_mpesa_message(msg)


def test_parse_fails_without_date():
    msg = "AB12CD34EF Confirmed. Ksh250.00 paid to ACME SUPERMARKET."
    with pytest.raises(ParseError):
        parse_mpesa_message(msg)