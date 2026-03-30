"""Load risk-control patterns and scan text for sensitive/competitor tokens.

Loads JSON config files under config/risk_control and compiles simple
regular-expression patterns to perform case-insensitive substring matching.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

CONFIG_DIR = Path(__file__).resolve().parents[1] / ".." / "config" / "risk_control"
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config" / "risk_control"


def _load_json(path: Path) -> List[str]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class RiskScanner:
    """Loads patterns from config and scans text for matches."""

    def __init__(self) -> None:
        base = CONFIG_DIR
        self.sensitive = _load_json(base / "sensitive_keywords.json")
        self.competitor = _load_json(base / "competitor_names.json")

        # compile simple word/substring patterns (escape special chars)
        self._sensitive_patterns = [
            re.compile(re.escape(s), re.IGNORECASE) for s in self.sensitive
        ]
        self._competitor_patterns = [
            re.compile(re.escape(c), re.IGNORECASE) for c in self.competitor
        ]

    def scan_text(self, raw_text: str) -> Tuple[List[str], List[str]]:
        """Return (matched_sensitive, matched_competitor) lists found in raw_text."""
        if not raw_text:
            return [], []

        matched_sensitive = set()
        matched_competitor = set()

        for pat, token in zip(self._sensitive_patterns, self.sensitive):
            if pat.search(raw_text):
                matched_sensitive.add(token)

        for pat, token in zip(self._competitor_patterns, self.competitor):
            if pat.search(raw_text):
                matched_competitor.add(token)

        return sorted(matched_sensitive), sorted(matched_competitor)


# module-level scanner for reuse
DEFAULT_SCANNER = RiskScanner()
