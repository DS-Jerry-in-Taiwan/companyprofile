import re


def clean_text(text):
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", "", text)
    # Remove special characters and excessive whitespace
    cleaned = re.sub(r"[\s\r\n]+", " ", cleaned)
    cleaned = re.sub(r"[^A-Za-z0-9 .,]", "", cleaned)
    return cleaned.strip()
