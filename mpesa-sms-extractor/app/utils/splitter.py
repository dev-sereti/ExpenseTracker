from __future__ import annotations

import re
from typing import List

TX_CODE_AT_START = re.compile(r"^[A-Z0-9]{6,15}\b")

def split_mpesa_messages(blob: str) -> List[str]:
    if not blob or not blob.strip():
        return []

    text = blob.strip()

    # Split by blank lines
    chunks = [c.strip() for c in re.split(r"\n\s*\n+", text) if c.strip()]
    if len(chunks) > 1:
        return chunks

    # Fallback: split by "transaction code at start of a line"
    lines = [ln.rstrip() for ln in text.splitlines()]
    messages: List[str] = []
    current: List[str] = []

    for ln in lines:
        if not ln.strip():
            continue

        if TX_CODE_AT_START.match(ln.strip()) and current:
            messages.append("\n".join(current).strip())
            current = [ln.strip()]
        else:
            current.append(ln.strip())

    if current:
        messages.append("\n".join(current).strip())

    # If we still somehow got nothing, treat entire blob as one message
    return [m for m in messages if m] or [text]