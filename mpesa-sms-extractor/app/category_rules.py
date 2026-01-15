from __future__ import annotations

from typing import Optional


# The list.
CATEGORY_CHOICES = [
    "Savings",
    "Lunch",
    "Mom",
    "Transport",
    "Internet",
    "Sis",
    "Cl&Sh",
    "Discretionary",
    "Health",
    "Authenticity",
    "Home",
    "Airtime",
    "Uncategorized",
]


# Keyword-based inference.
KEYWORD_RULES = [
    # keyword, category
    ("airtime", "Airtime"),
    ("bundle", "Internet"),
    ("data", "Internet"),
    ("kplc", "Home"),
    ("power", "Home"),
    ("rent", "Home"),
    ("uber", "Transport"),
    ("bolt", "Transport"),
    ("bus", "Transport"),
    ("matatu", "Transport"),
    ("fuel", "Transport"),
    ("hospital", "Health"),
    ("clinic", "Health"),
    ("nhif", "Health"),
    ("pharmacy", "Health"),
    ("shoe", "Cl&Sh"),
    ("clothes", "Cl&Sh"),
    ("saving", "Savings"),
    ("sacco", "Savings"),
    ("mum", "Mom"),
    ("mom", "Mom"),
    ("sister", "Sis"),
    ("sis", "Sis"),
]


def infer_category(
    recipient: Optional[str],
    sender: Optional[str],
    tx_type: str,
) -> Optional[str]:
    """
    Infer category from recipient/sender/transaction type using keyword rules.
    Returns a category name or None.
    """
    text_parts = [recipient or "", sender or "", tx_type or ""]
    text = " ".join(text_parts).lower()

    # Special case: airtime transaction type
    if tx_type.lower() == "airtime":
        return "Airtime"

    for keyword, category in KEYWORD_RULES:
        if keyword in text:
            return category

    return None