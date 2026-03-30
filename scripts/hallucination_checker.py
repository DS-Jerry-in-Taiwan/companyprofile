"""Hallucination checker skeleton.

This script provides a placeholder for comparing LLM-generated content
against known facts or the input sample to detect potential hallucinations.
It is intentionally a stub for Phase5 INFRA bootstrapping.
"""

from pathlib import Path
import json


def check_generated(sample_path: Path, result_path: Path) -> dict:
    # simplistic check: ensure the title or summary contains company_name
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    res = json.loads(result_path.read_text(encoding="utf-8"))
    company = sample.get("company_name", "").lower()
    summary = res.get("summary", "").lower()
    title = res.get("title", "").lower()
    flags = []
    if company and company not in summary and company not in title:
        flags.append("company_missing")
    return {"sample": sample_path.name, "flags": flags}


if __name__ == "__main__":
    # no-op demo
    print("hallucination_checker: run as helper in batch workflows")
