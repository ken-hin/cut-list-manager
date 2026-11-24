"""Checks for values typed into forms.

Each function either returns a clean value or raises ValidationError with a
message that can be shown to the user as-is.
"""
from datetime import date


class ValidationError(Exception):
    pass


def required_text(value, field_name):
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{field_name} is required.")
    return value


def optional_text(value):
    value = (value or "").strip()
    return value or None


def optional_phone(value, field_name):
    """Accept any formatting (865-555-0101, (865) 555 0101) and keep the 10 digits."""
    value = (value or "").strip()
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) != 10:
        raise ValidationError(f"{field_name} must be a 10-digit phone number.")
    return digits


def pickup_date(value):
    """Turn the date picker's YYYY-MM-DD text into a date."""
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        raise ValidationError("Pick a valid pickup date.")


def whole_number(value, field_name, minimum=None, maximum=None):
    try:
        number = int((value or "").strip())
    except ValueError:
        raise ValidationError(f"{field_name} must be a whole number.")
    if minimum is not None and number < minimum:
        raise ValidationError(f"{field_name} must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ValidationError(f"{field_name} must be at most {maximum}.")
    return number


def optional_positive_decimal(value, field_name):
    value = (value or "").strip()
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        raise ValidationError(f"{field_name} must be a number.")
    if number <= 0:
        raise ValidationError(f"{field_name} must be more than 0.")
    return number


def choice(value, allowed, field_name):
    if value not in allowed:
        raise ValidationError(f"Pick a valid {field_name}.")
    return value


def checkbox(form, name):
    """HTML checkboxes are only sent when checked."""
    return 1 if form.get(name) else 0
