"""Performance analysis utilities (placeholder).

Produces a short CSV summary from logs/token_costs.csv and logs/perf_logs.csv
"""

import csv
from pathlib import Path


def summarize_token_costs(path: Path):
    if not path.exists():
        print("No token cost log found:", path)
        return
    with path.open(encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        total = 0.0
        count = 0
        for row in r:
            try:
                total += float(row.get("estimated_cost", 0))
                count += 1
            except Exception:
                pass
        print("token cost entries=", count, "total_est_cost=", total)


if __name__ == "__main__":
    summarize_token_costs(Path("logs/token_costs.csv"))
