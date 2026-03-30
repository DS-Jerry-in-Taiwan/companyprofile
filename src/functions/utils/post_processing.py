# post_processing.py
"""
Post-processing Module
- HTML Sanitizer, Content Filter
"""
import bleach

SENSITIVE_WORDS = ['賭博', '情色']


def _filter_sensitive_text(text):
    filtered = text or ''
    for word in SENSITIVE_WORDS:
        filtered = filtered.replace(word, '***')
    return filtered


def post_process(llm_result):
    # HTML Sanitizer
    safe_html = bleach.clean(
        llm_result.get('body_html', ''),
        tags=['p', 'b', 'i', 'ul', 'li', 'br'],
        strip=True,
    )
    llm_result['body_html'] = _filter_sensitive_text(safe_html)
    llm_result['summary'] = _filter_sensitive_text(llm_result.get('summary', ''))
    llm_result['tags'] = [_filter_sensitive_text(tag) for tag in llm_result.get('tags', [])]
    return llm_result
