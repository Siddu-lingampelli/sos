"""Configurable distress-keyword matching (word-boundary, case-insensitive)."""
import re


def match_keywords(text: str, keywords) -> list[str]:
    """Return the subset of keywords found in text. Multi-word phrases supported."""
    low = text.lower()
    hits = []
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", low):
            hits.append(kw)
    return hits
