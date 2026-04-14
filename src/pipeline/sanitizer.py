"""Input sanitization: strip prompt-injection patterns from untrusted news text."""

from __future__ import annotations

import re

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"\[/INST\]", re.IGNORECASE),
]


def sanitize_text(text: str) -> tuple[str, bool]:
    """
    Strip known injection patterns from text.

    Returns (cleaned_text, was_modified).
    """
    modified = False
    cleaned = text
    for pattern in _INJECTION_PATTERNS:
        result = pattern.sub("", cleaned)
        if result != cleaned:
            modified = True
            cleaned = result
    cleaned = cleaned.strip()
    return cleaned, modified
