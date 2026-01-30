import re
from datetime import date
from typing import Annotated, Any
from pydantic import AfterValidator


def validate_clean_text(v: Any) -> str:
    if v is None or (isinstance(v, str) and not v.strip()):
        raise ValueError("Field cannot be empty or null")

    v = str(v).strip()
    if not re.match(r"^[a-zA-Zа-яА-Я0-9\s\-\.\(\)\&№,\/\+]+$", v):
        raise ValueError("Text contains prohibited special characters")

    if len(v) < 2:
        raise ValueError("Text must be at least 2 characters long")
    return v


def validate_strict_date(v: Any) -> date:
    if v is None:
        raise ValueError("Date is required and cannot be None")

    if not isinstance(v, date):
        raise ValueError("Invalid date format")

    if v > date.today():
        raise ValueError("Date cannot be in the future")

    if v.year < 2010:
        raise ValueError("Date is too far in the past")

    return v


def validate_email_strict(v: str) -> str:
    v = v.strip().lower()
    email_regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    if not re.match(email_regex, v):
        raise ValueError("Invalid email address")
    return v