# M-PESA SMS Extractor (FastAPI + PostgreSQL)

A server-rendered FastAPI web app that:
- Parses a pasted M-PESA SMS
- Extracts transaction details
- Stores them in PostgreSQL (deduped by transaction_code)
- Exports all stored transactions as an Excel (.xlsx)

## Run with Docker

1) Create `.env`:
```bash
cp .env.example .env