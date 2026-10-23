"""All SQL lives here. Functions take an open sqlite3 connection."""
import sqlite3
from datetime import date

FILTER_FIELDS = ("country", "department", "job_title", "employment_type")
SORT_COLUMNS = {
    "name": "e.name COLLATE NOCASE",
    "job_title": "e.job_title",
    "department": "e.department",
    "country": "e.country",
    "salary": "salary_usd",          # sort by normalised value so countries compare
    "hire_date": "e.hire_date",
}

# salary converted to USD at query time so FX changes apply retroactively.
SELECT_EMPLOYEE = """
    SELECT e.*, ROUND(e.salary * f.usd_per_unit) AS salary_usd
    FROM employees e JOIN fx_rates f ON f.currency = e.currency
"""


def _where(filters: dict, q: str | None) -> tuple[str, list]:
    clauses, params = [], []
    for field in FILTER_FIELDS:
        if filters.get(field):
            clauses.append(f"e.{field} = ?")
            params.append(filters[field])
    if q:
        escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        clauses.append("(e.name LIKE ? ESCAPE '\\' OR e.email LIKE ? ESCAPE '\\')")
        params += [like, like]
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def list_employees(conn, filters, q, sort, order, page, page_size):
    where, params = _where(filters, q)
    order_sql = SORT_COLUMNS.get(sort, SORT_COLUMNS["name"])
    direction = "DESC" if order == "desc" else "ASC"
    total = conn.execute(
        f"SELECT COUNT(*) FROM employees e{where}", params
    ).fetchone()[0]
    rows = conn.execute(
        f"{SELECT_EMPLOYEE}{where} ORDER BY {order_sql} {direction}, e.id "
        "LIMIT ? OFFSET ?",
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return [dict(r) for r in rows], total


def get_employee(conn, employee_id: int):
    row = conn.execute(f"{SELECT_EMPLOYEE} WHERE e.id = ?", (employee_id,)).fetchone()
    return dict(row) if row else None


def get_history(conn, employee_id: int):
    rows = conn.execute(
        "SELECT salary, currency, effective_date, note FROM salary_history "
        "WHERE employee_id = ? ORDER BY effective_date DESC, id DESC",
        (employee_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def create_employee(conn, data: dict) -> int:
    """Insert employee + initial history row in one transaction."""
    with conn:
        cur = conn.execute(
            "INSERT INTO employees (name,email,job_title,department,country,"
            "employment_type,salary,currency,hire_date) VALUES (?,?,?,?,?,?,?,?,?)",
            (data["name"], data["email"], data["job_title"], data["department"],
             data["country"], data["employment_type"], data["salary"],
             data["currency"], data["hire_date"]),
        )
        conn.execute(
            "INSERT INTO salary_history(employee_id,salary,currency,effective_date,note) "
            "VALUES (?,?,?,?,?)",
            (cur.lastrowid, data["salary"], data["currency"], data["hire_date"], "Starting salary"),
        )
    return cur.lastrowid


def update_employee(conn, employee_id: int, data: dict, today: date | None = None) -> bool:
    """Update; records a history row if salary or currency changed. False if not found."""
    today = today or date.today()
    with conn:
        old = conn.execute(
            "SELECT salary, currency FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
        if old is None:
            return False
        conn.execute(
            "UPDATE employees SET name=?, email=?, job_title=?, department=?, country=?,"
            "employment_type=?, salary=?, currency=?, hire_date=?, updated_at=datetime('now') "
            "WHERE id=?",
            (data["name"], data["email"], data["job_title"], data["department"],
             data["country"], data["employment_type"], data["salary"],
             data["currency"], data["hire_date"], employee_id),
        )
        if (old["salary"], old["currency"]) != (data["salary"], data["currency"]):
            conn.execute(
                "INSERT INTO salary_history(employee_id,salary,currency,effective_date,note) "
                "VALUES (?,?,?,?,?)",
                (employee_id, data["salary"], data["currency"], today.isoformat(),
                 f"Changed from {old['salary']} {old['currency']}"),
            )
    return True


def delete_employee(conn, employee_id: int) -> bool:
    with conn:
        cur = conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    return cur.rowcount > 0


def email_taken(conn, email: str, exclude_id: int | None = None) -> bool:
    row = conn.execute(
        "SELECT id FROM employees WHERE email = ? AND id IS NOT ?", (email, exclude_id)
    ).fetchone()
    return row is not None


def distinct_values(conn, field: str) -> list[str]:
    assert field in FILTER_FIELDS
    return [r[0] for r in conn.execute(
        f"SELECT DISTINCT {field} FROM employees ORDER BY {field} COLLATE NOCASE")]
