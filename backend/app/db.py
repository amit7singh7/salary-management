"""SQLite access: one connection per request, schema creation, FX seeding."""
import sqlite3
from flask import current_app, g

from .currency import USD_PER_UNIT

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    job_title       TEXT    NOT NULL,
    department      TEXT    NOT NULL,
    country         TEXT    NOT NULL,
    employment_type TEXT    NOT NULL CHECK (employment_type IN ('full_time','part_time','contract')),
    salary          INTEGER NOT NULL CHECK (salary > 0),   -- annual gross, whole local-currency units
    currency        TEXT    NOT NULL,
    hire_date       TEXT    NOT NULL,                      -- ISO date
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_emp_country    ON employees(country);
CREATE INDEX IF NOT EXISTS idx_emp_department ON employees(department);
CREATE INDEX IF NOT EXISTS idx_emp_job_title  ON employees(job_title);
CREATE INDEX IF NOT EXISTS idx_emp_name       ON employees(name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS salary_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id    INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    salary         INTEGER NOT NULL,
    currency       TEXT    NOT NULL,
    effective_date TEXT    NOT NULL,
    note           TEXT
);
CREATE INDEX IF NOT EXISTS idx_hist_emp ON salary_history(employee_id, effective_date);

CREATE TABLE IF NOT EXISTS fx_rates (
    currency     TEXT PRIMARY KEY,
    usd_per_unit REAL NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT OR IGNORE INTO fx_rates(currency, usd_per_unit) VALUES (?, ?)",
        USD_PER_UNIT.items(),
    )
    conn.commit()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
