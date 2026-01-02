from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from app.models import Transaction

HEADERS = ["Transaction Code", "Date", "Amount", "Mode", "Sender", "Receiver", "Raw Message"]


def transactions_to_xlsx(transactions: list[Transaction]) -> bytes:
    wb = Workbook()

    active = wb.active
    if active is None or not isinstance(active, Worksheet):
        ws: Worksheet = wb.create_sheet()
    else:
        ws = active

    ws.title = "Transactions"

    ws.append(HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True)

    for tx in transactions:
        ws.append(
            [
                tx.transaction_code,
                tx.transaction_date.isoformat(sep=" ", timespec="minutes"),
                float(tx.amount),
                tx.transaction_mode,
                tx.sender_name or "",
                tx.receiver_name or "",
                tx.raw_message,
            ]
        )

    widths = [18, 20, 12, 12, 22, 22, 60]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A2"

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()