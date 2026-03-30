"""Batch test runner for Phase5.

Scans JSON samples under data/test_samples/ and runs the current
risk control pipeline to produce outputs under outputs/generated_results/.

Usage:
  python scripts/batch_test.py --limit 20
"""

import argparse
import json
from pathlib import Path
from src.services.risk_control_service import RiskControlService


SAMPLES_DIR = Path("data/test_samples")
OUT_DIR = Path("outputs/generated_results")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_sample(p: Path):
    if p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    return {"sample_id": p.stem, "text": p.read_text(encoding="utf-8")}


def main(limit: int | None = None):
    svc = RiskControlService()
    files = sorted(SAMPLES_DIR.glob("*.json"))
    if not files:
        print("No JSON samples found in", SAMPLES_DIR)
        return
    if limit:
        files = files[:limit]
    for p in files:
        sample = load_sample(p)
        text = (
            sample.get("seed_query") or sample.get("description") or json.dumps(sample)
        )
        out = svc.scan_and_decide(text)
        outp = {
            "sample_id": sample.get("sample_id", p.stem),
            "title": out.title,
            "summary": out.summary,
            "risk_status": out.risk_status.value,
            "risk_level": out.risk_level.value,
            "matched_keywords": out.matched_keywords,
            "body_html": out.body_html,
        }
        (OUT_DIR / (p.stem + ".result.json")).write_text(
            json.dumps(outp, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("Processed", p.name, "->", p.stem + ".result.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    main(limit=args.limit)
