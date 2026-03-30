"""HTML sanitization wrapper using bleach.clean.

Provides a simple sanitize(html) function with allowed tags and attributes.
"""

from typing import List
import re
import html as _html

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

# only allow href/title on anchors; rel will be set defensively after cleaning
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}


def _remove_event_handlers(s: str) -> str:
    # remove attributes like onerror="..." or onclick='...'
    s = re.sub(r"\s+on\w+\s*=\s*\".*?\"", "", s, flags=re.I | re.S)
    s = re.sub(r"\s+on\w+\s*=\s*\'.*?\'", "", s, flags=re.I | re.S)
    return s


def _filter_href_schemes(s: str) -> str:
    # remove href attributes that are not http(s) or mailto
    def repl(m):
        url = m.group(1).strip()
        if re.match(r"^(https?:|mailto:)", url, flags=re.I):
            return f'href="{url}"'
        return ""

    s = re.sub(r'href\s*=\s*"([^"]*)"', repl, s, flags=re.I)
    s = re.sub(r"href\s*=\s*'([^']*)'", repl, s, flags=re.I)
    return s


def sanitize(html: str) -> str:
    """Sanitize raw HTML using bleach with pre-processing.

    Preprocessing steps:
    1. HTML-unescape entities
    2. Remove event-handler attributes (on...)
    3. Filter href schemes to allow only http(s) and mailto
    4. Run bleach.clean with allowed tags/attrs
    5. Add rel="nofollow" for anchors
    """
    if html is None:
        return ""

    # 1. decode entities (be careful not to introduce new executable code)
    decoded = _html.unescape(html)

    # 2. remove event handlers
    cleaned = _remove_event_handlers(decoded)

    # 3. filter href schemes
    cleaned = _filter_href_schemes(cleaned)

    # 4. sanitize with bleach
    out = bleach.clean(
        cleaned, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )

    # 5. ensure anchors have rel="nofollow"
    out = re.sub(
        r"<a\s+([^>]*href=[^>]*?)>",
        lambda m: "<a " + (m.group(1) + ' rel="nofollow"'),
        out,
        flags=re.I,
    )

    return out
