"""Text normalization utilities for risk scanning.

Provides functions to normalize text for robust matching against sensitive
keywords and competitor names. This includes Unicode NFKC normalization,
removal of zero-width characters, case folding, and simple homoglyph
mapping to handle common obfuscation (e.g., '1O4' -> '104').
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict


# Zero-width and control characters to remove
_ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200F\uFEFF\u2060\u180E]")

# Control characters (except newline and tab) to remove
_CONTROL_RE = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]")

# Simple homoglyph mapping (can be expanded)
_HOMOGLYPH_MAP: Dict[str, str] = {
    # common Latin homoglyphs -> ASCII
    "o": "0",
    "O": "0",
    "０": "0",
    "ｏ": "0",
    "Ｏ": "0",
    "l": "1",
    "I": "1",
    "i": "1",
    "Ｉ": "1",
    "１": "1",
    "ｌ": "1",
    "｜": "|",
    "S": "5",
    "s": "5",
    "Ｓ": "5",
}


def remove_zero_width(text: str) -> str:
    return _ZERO_WIDTH_RE.sub("", text)


def apply_homoglyph_map(text: str, mapping: Dict[str, str] | None = None) -> str:
    if mapping is None:
        mapping = _HOMOGLYPH_MAP
    # Simple character replacement
    return "".join(mapping.get(ch, ch) for ch in text)


def normalize_alnum(text: str) -> str:
    """Return a normalized string containing only ASCII alphanumeric characters.

    This helps detect tokens that have noise characters (punctuation, spaces,
    zero-width inserts) between alphanumerics.
    """
    s = normalize_text(text)
    # keep only letters and digits
    return "".join(ch for ch in s if ch.isalnum())


def normalize_text(text: str) -> str:
    """Normalize text for matching.

    Steps:
    1. Unicode NFKC normalization (converts fullwidth to halfwidth)
    2. Remove zero-width characters
    3. Case-fold for case-insensitive matching
    4. Apply simple homoglyph mapping
    """
    if text is None:
        return ""
    s = unicodedata.normalize("NFKC", text)
    # remove zero-width and control characters that attackers may use
    s = remove_zero_width(s)
    s = _CONTROL_RE.sub("", s)
    # apply casefold to be aggressive for international text
    s = s.casefold()
    s = apply_homoglyph_map(s)
    return s


def normalize_token_for_index(token: str) -> str:
    """Normalize a keyword/token using the same rules (keeps mapping)."""
    return normalize_text(token)
