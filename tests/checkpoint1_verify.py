#!/usr/bin/env python3
"""
Checkpoint 1 verification script

Runs a lightweight verification of Phase 4 risk control strategy using
the current config files in config/risk_control/. This is intended for
CheckPoint 1 review: validate configs are present, schemas exist, and
sample inputs exercise detection and sanitization logic.

Usage:
  source .venv/bin/activate
  python tests/checkpoint1_verify.py

This script is NOT the final risk_control_service implementation but a
validator to confirm ARCH decisions before CODER implements the full service.
"""

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import bleach

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config" / "risk_control"


def load_json(name: str):
    path = CONFIG_DIR / name
    if not path.exists():
        print(f"[ERROR] Missing config: {path}")
        sys.exit(2)
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    # NFKC + casefold for robust matching
    return unicodedata.normalize("NFKC", text).casefold()


def compile_patterns(keywords):
    patterns = []
    for kw in keywords:
        k = normalize(kw)
        # use simple substring and word-boundary pattern fallback
        try:
            p = re.compile(rf"(?<!\w)({re.escape(k)})(?!\w)", flags=re.IGNORECASE)
        except re.error:
            p = re.compile(re.escape(k), flags=re.IGNORECASE)
        patterns.append((kw, p))
    return patterns


def mask_competitors(text: str, competitor_patterns, strategy: str = "mask") -> str:
    out = text
    for kw, pat in competitor_patterns:
        if strategy == "mask":
            out = pat.sub("***", out)
        elif strategy == "preserve_length":

            def repl(m):
                return "*" * len(m.group(0))

            out = pat.sub(repl, out)
        else:
            out = pat.sub("", out)
    return out


def scan(text: str, sensitive_patterns, competitor_patterns):
    n = normalize(text)
    matched_sensitive = []
    matched_competitor = []
    for kw, pat in sensitive_patterns:
        # For CJK and other scripts where word-boundary may fail, also check substring
        if pat.search(n) or normalize(kw) in n:
            matched_sensitive.append(kw)
    for kw, pat in competitor_patterns:
        if pat.search(n) or normalize(kw) in n:
            matched_competitor.append(kw)
    return matched_sensitive, matched_competitor


def sanitize_html(html: str):
    # keep a minimal whitelist consistent with ARCH recommendations
    allowed_tags = ["p", "a", "strong", "em", "ul", "ol", "li", "br"]
    allowed_attrs = {"a": ["href", "title"]}
    cleaned = bleach.clean(
        html, tags=allowed_tags, attributes=allowed_attrs, strip=True
    )
    return cleaned


def run_samples():
    sensitive = load_json("sensitive_keywords.json")
    competitors = load_json("competitor_names.json")

    sensitive_patterns = compile_patterns(sensitive)
    competitor_patterns = compile_patterns(competitors)

    samples_dir = ROOT / "tests" / "samples"
    samples = list(samples_dir.glob("*"))
    if not samples:
        print("[WARN] No samples found under tests/samples/")
        return 1

    expectations = {
        "gambling.txt": "PENDING",
        "competitor.txt": "PENDING",
        "xss.html": "APPROVED_SANITIZED",
        "clean.txt": "APPROVED",
    }

    overall_ok = True
    for f in samples:
        name = f.name
        raw = f.read_text(encoding="utf-8")
        print("\n---")
        print(f"Sample: {name}")
        matched_s, matched_c = scan(raw, sensitive_patterns, competitor_patterns)
        sanitized = sanitize_html(raw)
        masked = mask_competitors(sanitized, competitor_patterns, strategy="mask")

        decision = "APPROVED"
        if matched_s:
            decision = "PENDING"
        if matched_c:
            decision = "PENDING"

        print(f"Matched sensitive: {matched_s}")
        print(f"Matched competitor: {matched_c}")
        print(f"Sanitized (snippet): {sanitized[:200]!r}")
        print(f"Masked (snippet): {masked[:200]!r}")
        print(f"Decision (simple): {decision}")

        expected = expectations.get(name)
        ok = True
        if expected:
            if expected == "APPROVED_SANITIZED":
                ok = "<script" not in sanitized.lower()
            elif expected == "APPROVED":
                ok = (not matched_s) and (not matched_c)
            else:
                ok = decision == expected
        print(f"Expected: {expected} => {'PASS' if ok else 'FAIL'}")
        overall_ok = overall_ok and ok

    print("\n=== Summary ===")
    print(f"All samples pass expectations: {overall_ok}")
    return 0 if overall_ok else 3


if __name__ == "__main__":
    rc = run_samples()
    sys.exit(rc)
