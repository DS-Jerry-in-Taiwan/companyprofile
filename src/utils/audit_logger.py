"""Simple audit logger for risk control events.

Writes JSON lines to a log file under logs/risk_audit.log. This is a
minimal implementation for MVP; can be swapped for structured logging or
database-backed audit storage later.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "risk_audit.log"


def log_event(event: Dict) -> None:
    """Append an audit event (dict) as a JSON line to the audit log."""
    e = event.copy()
    if "timestamp" not in e:
        e["timestamp"] = datetime.utcnow().isoformat() + "Z"
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(e, ensure_ascii=False) + "\n")
