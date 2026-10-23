"""HTTP layer: parse input, call validation/repository, shape JSON."""
from flask import Blueprint, jsonify, request

from . import repository as repo
from .currency import COUNTRY_CURRENCY
from .db import get_db
from .validation import EMPLOYMENT_TYPES, ValidationError, validate_employee

bp = Blueprint("api", __name__, url_prefix="/api")

MAX_PAGE_SIZE = 100


@bp.errorhandler(ValidationError)
def _validation_error(exc):
    return jsonify(error="validation_failed", fields=exc.errors), 422


def _not_found():
    return jsonify(error="not_found"), 404


def _int_arg(name, default, lo, hi):
    try:
        value = int(request.args.get(name, default))
    except ValueError:
        value = default
    return max(lo, min(hi, value))


def _filters_from_query() -> dict:
    return {f: request.args.get(f) for f in repo.FILTER_FIELDS if request.args.get(f)}


def _check_email_unique(db, email, exclude_id=None):
    if repo.email_taken(db, email, exclude_id):
        raise ValidationError({"email": "Another employee already uses this email."})


@bp.get("/meta")
def meta():
    db = get_db()
    return jsonify(
        countries=[{"name": c, "currency": cur} for c, cur in COUNTRY_CURRENCY.items()],
        employment_types=list(EMPLOYMENT_TYPES),
        departments=repo.distinct_values(db, "department"),
        job_titles=repo.distinct_values(db, "job_title"),
    )


@bp.get("/employees")
def list_employees():
    page = _int_arg("page", 1, 1, 10**6)
    page_size = _int_arg("page_size", 25, 1, MAX_PAGE_SIZE)
    items, total = repo.list_employees(
        get_db(), _filters_from_query(), request.args.get("q"),
        request.args.get("sort", "name"), request.args.get("order", "asc"),
        page, page_size,
    )
    return jsonify(items=items, total=total, page=page, page_size=page_size)


@bp.post("/employees")
def create_employee():
    data = validate_employee(request.get_json(silent=True))
    db = get_db()
    _check_email_unique(db, data["email"])
    new_id = repo.create_employee(db, data)
    return jsonify(repo.get_employee(db, new_id)), 201


@bp.get("/employees/<int:employee_id>")
def get_employee(employee_id):
    db = get_db()
    emp = repo.get_employee(db, employee_id)
    if emp is None:
        return _not_found()
    emp["history"] = repo.get_history(db, employee_id)
    return jsonify(emp)


@bp.put("/employees/<int:employee_id>")
def update_employee(employee_id):
    data = validate_employee(request.get_json(silent=True))
    db = get_db()
    _check_email_unique(db, data["email"], exclude_id=employee_id)
    if not repo.update_employee(db, employee_id, data):
        return _not_found()
    emp = repo.get_employee(db, employee_id)
    emp["history"] = repo.get_history(db, employee_id)
    return jsonify(emp)


@bp.delete("/employees/<int:employee_id>")
def delete_employee(employee_id):
    if not repo.delete_employee(get_db(), employee_id):
        return _not_found()
    return "", 204


# ---- insights -------------------------------------------------------------
from . import insights  # noqa: E402


@bp.get("/summary")
def summary():
    return jsonify(insights.company_summary(get_db(), _filters_from_query()))


@bp.get("/insights")
def pay_insights():
    group_by = request.args.get("group_by", "country")
    if group_by not in insights.GROUP_BY_FIELDS:
        return jsonify(error="invalid_group_by",
                       allowed=list(insights.GROUP_BY_FIELDS)), 400
    return jsonify(group_by=group_by,
                   groups=insights.group_stats(get_db(), group_by, _filters_from_query()))


@bp.get("/insights/distribution")
def pay_distribution():
    return jsonify(buckets=insights.distribution(get_db(), _filters_from_query()),
                   bucket_width_usd=insights.BUCKET_USD)
