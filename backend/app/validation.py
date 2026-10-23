"""Input validation for employee payloads. Pure functions: no DB, no Flask."""
import re
from datetime import date

from .currency import COUNTRY_CURRENCY

EMPLOYMENT_TYPES = ("full_time", "part_time", "contract")
MAX_SALARY = 10_000_000_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        super().__init__("validation failed")
        self.errors = errors


def _text(data, field, errors, max_len=100):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors[field] = "Required."
        return None
    value = " ".join(value.split())
    if len(value) > max_len:
        errors[field] = f"Must be {max_len} characters or fewer."
        return None
    return value


def validate_employee(data: dict, today: date | None = None) -> dict:
    """Return a cleaned employee dict (with derived currency) or raise ValidationError."""
    if not isinstance(data, dict):
        raise ValidationError({"_": "Body must be a JSON object."})
    today = today or date.today()
    errors: dict[str, str] = {}

    name = _text(data, "name", errors)
    job_title = _text(data, "job_title", errors)
    department = _text(data, "department", errors)

    email = _text(data, "email", errors, max_len=254)
    if email is not None:
        email = email.lower()
        if not _EMAIL_RE.match(email):
            errors["email"] = "Enter a valid email address."

    country = data.get("country")
    if country not in COUNTRY_CURRENCY:
        errors["country"] = "Choose a supported country."
        country = None

    employment_type = data.get("employment_type")
    if employment_type not in EMPLOYMENT_TYPES:
        errors["employment_type"] = "Must be full_time, part_time or contract."
        employment_type = None

    salary = data.get("salary")
    # bool is a subclass of int; reject it explicitly. Accept whole numbers only.
    if isinstance(salary, float) and salary.is_integer():
        salary = int(salary)
    if isinstance(salary, bool) or not isinstance(salary, int):
        errors["salary"] = "Enter the annual salary as a whole number."
        salary = None
    elif not 0 < salary <= MAX_SALARY:
        errors["salary"] = "Must be greater than 0."
        salary = None

    hire_date = data.get("hire_date")
    try:
        parsed = date.fromisoformat(hire_date) if isinstance(hire_date, str) else None
    except ValueError:
        parsed = None
    if parsed is None:
        errors["hire_date"] = "Use the format YYYY-MM-DD."
    elif parsed > today:
        errors["hire_date"] = "Hire date cannot be in the future."

    if errors:
        raise ValidationError(errors)

    return {
        "name": name,
        "email": email,
        "job_title": job_title,
        "department": department,
        "country": country,
        "employment_type": employment_type,
        "salary": salary,
        "currency": COUNTRY_CURRENCY[country],
        "hire_date": hire_date,
    }
