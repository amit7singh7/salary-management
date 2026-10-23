"""Pay insights. `percentile`/`summarize` are pure; `group_stats` etc. query the DB.

Medians/percentiles are computed in Python rather than SQL because SQLite has no
percentile function; for 10k rows this is a few milliseconds.
"""
from collections import defaultdict

from . import repository as repo

GROUP_BY_FIELDS = ("country", "department", "job_title", "employment_type")
BUCKET_USD = 25_000
MAX_BUCKET_USD = 250_000  # everything above falls into the last, open-ended bucket


def percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (same as numpy's default). pct in [0, 100]."""
    if not sorted_values:
        raise ValueError("percentile of empty list")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (pct / 100) * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


def summarize(values: list[float]) -> dict:
    vals = sorted(values)
    return {
        "headcount": len(vals),
        "min": round(vals[0]),
        "p25": round(percentile(vals, 25)),
        "median": round(percentile(vals, 50)),
        "p75": round(percentile(vals, 75)),
        "max": round(vals[-1]),
        "average": round(sum(vals) / len(vals)),
    }


def _filtered_rows(conn, filters: dict):
    where, params = repo._where(filters, None)
    return conn.execute(
        "SELECT e.country, e.department, e.job_title, e.employment_type, "
        "e.salary, e.currency, e.salary * f.usd_per_unit AS salary_usd "
        "FROM employees e JOIN fx_rates f ON f.currency = e.currency" + where,
        params,
    ).fetchall()


def group_stats(conn, group_by: str, filters: dict) -> list[dict]:
    """Per-group pay statistics in USD; plus local-currency stats when a group
    has a single currency (e.g. every country, or a single-country filter)."""
    if group_by not in GROUP_BY_FIELDS:
        raise ValueError(f"group_by must be one of {GROUP_BY_FIELDS}")
    usd: dict[str, list[float]] = defaultdict(list)
    local: dict[str, list[float]] = defaultdict(list)
    currencies: dict[str, set] = defaultdict(set)
    for row in _filtered_rows(conn, filters):
        key = row[group_by]
        usd[key].append(row["salary_usd"])
        local[key].append(row["salary"])
        currencies[key].add(row["currency"])

    out = []
    for key, values in usd.items():
        entry = {"group": key, **summarize(values)}
        if len(currencies[key]) == 1:
            entry["currency"] = next(iter(currencies[key]))
            entry["local"] = summarize(local[key])
        out.append(entry)
    out.sort(key=lambda e: e["median"], reverse=True)
    return out


def distribution(conn, filters: dict) -> list[dict]:
    """Histogram of USD salaries in fixed-width buckets (last bucket open-ended)."""
    n_buckets = MAX_BUCKET_USD // BUCKET_USD + 1
    counts = [0] * n_buckets
    for row in _filtered_rows(conn, filters):
        counts[min(int(row["salary_usd"] // BUCKET_USD), n_buckets - 1)] += 1
    out = []
    for i, count in enumerate(counts):
        lo = i * BUCKET_USD
        out.append({"from": lo, "to": None if i == n_buckets - 1 else lo + BUCKET_USD,
                    "count": count})
    return out


def company_summary(conn, filters: dict | None = None) -> dict:
    rows = _filtered_rows(conn, filters or {})
    if not rows:
        return {"headcount": 0, "total_payroll_usd": 0, "countries": 0, "departments": 0}
    return {
        "headcount": len(rows),
        "total_payroll_usd": round(sum(r["salary_usd"] for r in rows)),
        "countries": len({r["country"] for r in rows}),
        "departments": len({r["department"] for r in rows}),
        **{k: v for k, v in summarize([r["salary_usd"] for r in rows]).items()
           if k in ("median", "average")},
    }
