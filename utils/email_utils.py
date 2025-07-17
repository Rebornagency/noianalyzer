# utils/email_utils.py
"""Email validation utilities for NOI Analyzer.

Provides:
- is_valid_email(email): basic RFC-style regex validation
- is_disposable_email(email): check against common disposable domains list

These helpers let the credit system block throw-away addresses from getting
free trial credits.
"""
from __future__ import annotations

import re
from functools import lru_cache

# Simple RFC-5322 email regex (not perfect but good enough)
_EMAIL_REGEX = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)

# Minimal curated list of disposable email domains.  Expand as needed.
_DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "getnada.com",
    "trashmail.com",
    "yopmail.com",
    "sharklasers.com",
    "spamgourmet.com",
    "maildrop.cc",
    "fakeinbox.com",
}

def is_valid_email(email: str) -> bool:
    """Return True if *email* looks like a syntactically valid address."""
    return bool(_EMAIL_REGEX.match(email or ""))

@lru_cache(maxsize=1024)
def is_disposable_email(email: str) -> bool:
    """Return True if the email's domain is in the disposable list."""
    if not email:
        return True
    try:
        domain = email.split("@", 1)[1].lower()
    except IndexError:
        return True
    return domain in _DISPOSABLE_DOMAINS 