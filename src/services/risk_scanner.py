"""Load risk-control patterns and scan text for sensitive/competitor tokens.

Loads JSON config files under config/risk_control and compiles simple
regular-expression patterns to perform case-insensitive substring matching.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

from src.utils.text_normalizer import normalize_text

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config" / "risk_control"


def _load_json(path: Path) -> List[str]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class RiskScanner:
    """Loads patterns from config and scans text for matches.

    This scanner normalizes both the configured keywords and the input text
    using a shared normalization function to improve robustness against
    common obfuscation techniques.
    """

    def __init__(self) -> None:
        base = CONFIG_DIR
        self.sensitive = _load_json(base / "sensitive_keywords.json")
        self.competitor = _load_json(base / "competitor_names.json")

        # normalize keywords for matching
        self._sensitive_norm = [normalize_text(s) for s in self.sensitive]
        self._competitor_norm = [normalize_text(c) for c in self.competitor]

        # compile simple substring patterns on normalized tokens
        self._sensitive_patterns = [
            re.compile(re.escape(s)) for s in self._sensitive_norm
        ]
        self._competitor_patterns = [
            re.compile(re.escape(c)) for c in self._competitor_norm
        ]

    def scan_text(self, raw_text: str) -> Tuple[List[str], List[str]]:
        """Return (matched_sensitive, matched_competitor) lists found in raw_text.

        Matching is performed on normalized text and returns the original
        configured tokens that matched.
        """
        if not raw_text:
            return [], []

        n = normalize_text(raw_text)

        matched_sensitive = set()
        matched_competitor = set()

        for norm_pat, orig_token in zip(self._sensitive_patterns, self.sensitive):
            if norm_pat.search(n):
                matched_sensitive.add(orig_token)

        for norm_pat, orig_token in zip(self._competitor_patterns, self.competitor):
            if norm_pat.search(n):
                matched_competitor.add(orig_token)

        return sorted(matched_sensitive), sorted(matched_competitor)


# module-level scanner for reuse
DEFAULT_SCANNER = RiskScanner()
