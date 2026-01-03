# M-PESA SMS Extractor, Transaction Manager & Dashboard

A production-ready **web-based** M-PESA transaction manager built with **FastAPI + Jinja2 + PostgreSQL**.

Paste an M-PESA SMS into the web UI, the app extracts structured transaction details, stores them in PostgreSQL (with deduplication), lets you browse/search transactions, export to Excel, and view an interactive dashboard focusing on the **last 3 months**.

---

## Table of contents

- [What this app does](#what-this-app-does)
- [Features](#features)
- [Screens and routes](#screens-and-routes)
- [Tech stack](#tech-stack)
- [Data model](#data-model)
- [Parsing behavior](#parsing-behavior)
- [Dashboard analytics](#dashboard-analytics)
- [Project structure](#project-structure)
- [Docker Compose quickstart](#docker-compose-quickstart)
- [Environment variables](#environment-variables)
- [Database migrations](#database-migrations)
- [Running tests](#running-tests)
- [Local development without Docker](#local-development-without-docker)
- [Troubleshooting](#troubleshooting)
- [Security and privacy notes](#security-and-privacy-notes)
- [Production notes](#production-notes)
- [Roadmap](#roadmap)
- [License](#license)

---

## What this app does

1. You open the web app.
2. You paste a **single M-PESA SMS** into a textarea and click **Extract & Save**.
3. The app parses the SMS and extracts:
   - `transaction_code` (e.g. `QW12ABC3DE`)
   - `transaction_date` (timezone-aware datetime; assumes **Africa/Nairobi**)
   - `amount` (stored as `DECIMAL(12,2)` in PostgreSQL)
   - `transaction_mode` (`Received`, `Sent`, `Paid`, `Withdraw`, `Deposit`, `Reversal`, `Other`)
   - `sender_name` (nullable)
   - `receiver_name` (nullable)
   - `raw_message` (stored exactly as pasted for audit/debug)
4. It saves the parsed transaction to PostgreSQL.
5. You can view saved transactions and download an **Excel (.xlsx)** export.
6. You can view a dashboard summarizing totals and trends for the **last 3 months**.

---

## Features

- **Server-rendered web UI** (FastAPI + Jinja2 templates)
- **Robust-ish parsing** using regex + normalization
- **Deduplication**: same `transaction_code` pasted twice will not create duplicates
- **Transactions list view** with simple search by transaction code
- **Excel export** via `openpyxl`
- **Interactive dashboard** (Chart.js via CDN):
  - Total `Sent`, `Received`, and `Paid` amounts
  - Monthly totals (last 3 months)
  - Cumulative totals across the last 3 months
  - Period mix doughnut chart (Received vs Sent vs Paid)
- **PostgreSQL** persistence using **SQLAlchemy 2.0**
- **Alembic migrations**
- **Docker + docker-compose** (web + postgres)
- **pytest** unit tests for the parser

---

## Screens and routes

- `GET /`  
  Paste an SMS and click **Extract & Save**.

- `POST /`  
  Parses and saves (or shows validation error / “Transaction already exists”).

- `GET /transactions`  
  Table of saved transactions (most recent first). Optional search: `?q=QW12`

- `GET /export.xlsx`  
  Downloads Excel export of transactions. Optional:
  - `?start=YYYY-MM-DD`
  - `?end=YYYY-MM-DD`

- `GET /dashboard`  
  Dashboard for the last 3 months (totals + charts).

- `GET /healthz`  
  Basic health check.

---

## Tech stack

- Python **3.11+**
- FastAPI
- Jinja2 templates
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- openpyxl (Excel export)
- Chart.js (dashboard charts via CDN)
- Docker + docker-compose

---

## Data model

Table: `transactions`

Minimum columns:

- `id` (PK)
- `transaction_code` (unique index)
- `transaction_date` (timestamp with timezone)
- `amount` (DECIMAL(12,2))
- `transaction_mode` (string)
- `sender_name` (nullable)
- `receiver_name` (nullable)
- `raw_message` (text)
- `created_at` (timestamp)

Constraint:
- `transaction_code` is unique → prevents duplicates. If you paste the same SMS twice, the UI shows:
  - **“Transaction already exists: <code>.”**

---

## Parsing behavior

The parser is designed to handle common M-PESA message styles (not exhaustive). It uses:
- first token as transaction code
- regex extraction for amount (`Ksh1,000.00`, `Ksh 1000`, etc.)
- regex extraction for date/time:
  - `on 2/1/24 at 3:45 PM` (day/month/year)

Mode detection is keyword-based:
- `sent to` → **Sent**
- `received ... from` → **Received**
- `paid to` → **Paid**
- otherwise → **Other** (plus basic support for Withdraw/Deposit/Reversal keywords)

Sender/receiver rules:
- Sent: receiver after `sent to ...`
- Received: sender after `from ...`
- Paid: receiver after `paid to ...`
- If sender/receiver cannot be found, they are stored as `NULL` and the transaction still saves (as long as code/amount/date exist).

Validation:
- If `transaction_code` OR `amount` OR `transaction_date` is missing → the app will **not save** and will show a clear error.

---

## Dashboard analytics

The dashboard focuses on the **last 3 months (including the current month)** and provides:

- Totals over the window:
  - Received total
  - Sent total
  - Paid total
  - Net = Received − (Sent + Paid)

- Monthly totals chart (bar)
- Cumulative chart (line), which shows running totals across those 3 months
- Mix chart (doughnut): Received vs Sent vs Paid totals for the window

Charts are rendered with Chart.js (CDN) in `dashboard.html`.
