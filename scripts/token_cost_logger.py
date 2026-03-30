"""Token / cost logger placeholder.

This script is a lightweight helper to record token usage and estimated cost
for a given set of requests. It is intentionally simple for Phase5 INFRA
bootstrap; analytic improvements can be added by @ANALYST later.
"""

import csv
from pathlib import Path

OUT = Path("logs/token_costs.csv")
OUT.parent.mkdir(exist_ok=True)


def log(entry: dict):
    headers = ["timestamp", "sample_id", "tokens_in", "tokens_out", "estimated_cost"]
    write_header = not OUT.exists()
    with OUT.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=headers)
        if write_header:
            w.writeheader()
        w.writerow({k: entry.get(k, "") for k in headers})


if __name__ == "__main__":
    # example
    from datetime import datetime

    log(
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sample_id": "sample-000",
            "tokens_in": 123,
            "tokens_out": 456,
            "estimated_cost": 0.0123,
        }
    )
    print("wrote sample token cost to", OUT)
