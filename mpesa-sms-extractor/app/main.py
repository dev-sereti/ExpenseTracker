from __future__ import annotations

import os
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.parser import parse_mpesa_message, ParseError
from app.services.transactions import create_transaction, list_transactions, get_all_transactions
from app.services.excel import transactions_to_xlsx


app = FastAPI(title="M-PESA SMS Extractor", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message_text": "",
            "parsed": None,
            "success": None,
            "error": None,
        },
    )


@app.post("/", response_class=HTMLResponse)
def extract_and_save(
    request: Request,
    message_text: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    raw = message_text.strip()
    try:
        parsed = parse_mpesa_message(raw)
    except ParseError as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "message_text": raw,
                "parsed": None,
                "success": None,
                "error": str(e),
            },
            status_code=400,
        )

    created, tx = create_transaction(db, parsed, raw)
    if created:
        success = f"Saved transaction {tx.transaction_code}."
    else:
        success = f"Transaction already exists: {tx.transaction_code}."

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message_text": raw,
            "parsed": parsed.model_dump(),
            "success": success,
            "error": None,
        },
    )


@app.get("/transactions", response_class=HTMLResponse)
def transactions_page(
    request: Request,
    q: Optional[str] = Query(default=None, description="Transaction code search"),
    db: Session = Depends(get_db),
):
    rows = list_transactions(db, q=q)
    return templates.TemplateResponse(
        "transactions.html",
        {"request": request, "transactions": rows, "q": q or ""},
    )


@app.get("/export.xlsx")
def export_xlsx(
    db: Session = Depends(get_db),
    start: Optional[date] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end: Optional[date] = Query(default=None, description="End date (YYYY-MM-DD)"),
):
    # Simple optional date filtering using transaction_date date-part in Python after query,
    # keeping DB query straightforward and portable.
    txs = get_all_transactions(db)
    if start:
        txs = [t for t in txs if t.transaction_date.date() >= start]
    if end:
        txs = [t for t in txs if t.transaction_date.date() <= end]

    content = transactions_to_xlsx(txs)
    filename = f"mpesa-transactions-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.xlsx"

    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/healthz")
def healthz():
    return {"ok": True}