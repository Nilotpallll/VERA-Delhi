"""Input sanitization, prompt injection detection, and post-generation safety guards."""

import re
import unicodedata

from .policy import (
    REFUSAL_INVESTMENT_ADVICE_EN,
    REFUSAL_INVESTMENT_ADVICE_HI,
)

# Zero-width and invisible characters
ZERO_WIDTH_CHARS = re.compile(r"[\u200B-\u200D\uFEFF\u00A0\u202A-\u202E]")

# PII Patterns: 12-digit Indian Aadhaar number, 16-digit card number
AADHAAR_REGEX = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")
CARD_REGEX = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

# Prompt Injection Triggers
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|system)\s+rules", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(dan|unrestricted|godmode)", re.IGNORECASE),
    re.compile(r"(reveal|print|show)\s+(your\s+)?(system\s+prompt|secret\s+key|api\s+key)", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|content)\s+filters?", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]

# Investment Advice Violation Triggers in Output
STOCK_ADVICE_OUTPUT_TRIGGERS = [
    re.compile(r"\b(buy|sell|accumulate|hold)\s+shares?\s+of\b", re.IGNORECASE),
    re.compile(r"\btarget\s+price\s+of\s+rs\.?\s*\d+", re.IGNORECASE),
    re.compile(r"\bguaranteed\s+(return|profit|gains?)\b", re.IGNORECASE),
    re.compile(r"\binvest\s+your\s+money\s+in\s+[A-Z]{3,}\b", re.IGNORECASE),
]


def sanitize_input(text: str, max_chars: int = 500) -> str:
    """Cleans text of invisible unicode, control characters, and truncates length."""
    if not text:
        return ""
    # Strip zero-width & bidirectional overrides
    cleaned = ZERO_WIDTH_CHARS.sub("", text)
    # Normalize unicode to NFC
    cleaned = unicodedata.normalize("NFC", cleaned)
    # Strip unprintable control characters except newline and tab
    cleaned = "".join(ch for ch in cleaned if ch in ("\n", "\t") or not unicodedata.category(ch).startswith("C"))
    # Truncate
    cleaned = cleaned[:max_chars].strip()
    return cleaned


def mask_pii(text: str) -> str:
    """Masks Aadhaar numbers and card numbers to protect user privacy before processing."""
    masked = CARD_REGEX.sub("[REDACTED_CARD]", text)
    masked = AADHAAR_REGEX.sub("[REDACTED_ID]", masked)
    return masked


def check_prompt_injection(text: str) -> bool:
    """Returns True if the text matches known prompt injection signatures."""
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def filter_generated_output(text: str, language: str = "en") -> tuple[str, bool]:
    """Inspects LLM output for policy violations.

    If violations are found, replaces text with the appropriate safe refusal.
    Returns (filtered_text, was_flagged).
    """
    for pattern in STOCK_ADVICE_OUTPUT_TRIGGERS:
        if pattern.search(text):
            refusal = REFUSAL_INVESTMENT_ADVICE_HI if language == "hi" else REFUSAL_INVESTMENT_ADVICE_EN
            return refusal, True

    return text, False
