"""HTML sanitization wrapper using bleach.clean.

Provides a simple sanitize(html) function with allowed tags and attributes.
"""

from typing import List

import bleach


ALLOWED_TAGS: List[str] = [
    "p",
    "b",
    "i",
    "u",
    "a",
    "ul",
    "li",
    "ol",
    "br",
    "strong",
    "em",
]

ALLOWED_ATTRIBUTES = {"a": ["href", "title", "rel"]}


def sanitize(html: str) -> str:
    """Sanitize raw HTML using bleach and return safe HTML string.

    This function strips disallowed tags/attributes and ensures output is safe
    for rendering in UIs.
    """
    if html is None:
        return ""
    return bleach.clean(
        html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )
