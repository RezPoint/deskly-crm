import re
from typing import Optional

_PHONE_ALLOWED = re.compile(r"^[+\d\s()\-]{3,25}$")
_TELEGRAM_ALLOWED = re.compile(r"^[A-Za-z0-9_]{5,32}$")
_EMAIL_ALLOWED = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_phone(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    phone = value.strip()
    if not phone:
        return None
    if not _PHONE_ALLOWED.match(phone):
        raise ValueError("phone must contain digits and optional +, -, spaces, or parentheses")
    digits = [c for c in phone if c.isdigit()]
    if len(digits) < 3 or len(digits) > 15:
        raise ValueError("phone must contain 3-15 digits")
    return phone


def validate_telegram(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    handle = value.strip()
    if not handle:
        return None
    if handle.startswith("@"):
        handle = handle[1:]
    if not _TELEGRAM_ALLOWED.match(handle):
        raise ValueError("telegram must be 5-32 chars: letters, numbers, underscore")
    return f"@{handle}"


def validate_email(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    email = value.strip().lower()
    if not email:
        return None
    if not _EMAIL_ALLOWED.match(email):
        raise ValueError("email must be a valid address")
    return email
