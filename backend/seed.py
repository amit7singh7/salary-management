"""Seed the database with realistic, deterministic employees.

    python seed.py              # 10,000 employees (refuses if DB already has data)
    python seed.py --reset      # wipe employees first
    python seed.py -n 500 --seed 7
"""
import argparse
import random
from datetime import date, timedelta

from app import db
from app.currency import COUNTRY_CURRENCY, USD_PER_UNIT

FIRST = ("Aarav Aditi Akira Alex Amelia Ana Anders Ben Carlos Chen Chloe Daniel Elena Emma "
         "Fatima Gabriel Hana Isabella Ivan Jack Jin Kavya Kenji Lars Leila Liam Lucas Maya "
         "Mohammed Nadia Noah Olivia Omar Priya Rahul Sofia Sana Tomasz Wei Yara Zoe").split()
LAST = ("Almeida Anderson Banerjee Bauer Brown Chen Costa Das Dubois Fischer Garcia Gupta "
        "Hassan Ito Jensen Johnson Kim Kowalski Kumar Lee Martin Miller Nakamura Nguyen "
        "Novak Okafor Patel Rao Reddy Rossi Sato Schmidt Silva Singh Smith Tan Wang "
        "Williams Wilson Yamamoto Zhang").split()

# department -> [(title, base USD for a US-level salary)]
ROLES = {
    "Engineering": [("Software Engineer", 120_000), ("Senior Software Engineer", 160_000),
                    ("Staff Engineer", 200_000), ("QA Engineer", 90_000),
                    ("DevOps Engineer", 125_000), ("Engineering Manager", 190_000)],
    "Product": [("Product Manager", 135_000), ("Senior Product Manager", 170_000),
                ("Product Designer", 110_000), ("Director of Product", 210_000)],
    "Sales": [("Account Executive", 95_000), ("Sales Development Rep", 62_000),
              ("Sales Manager", 140_000), ("Solutions Engineer", 115_000)],
    "Marketing": [("Marketing Specialist", 70_000), ("Content Strategist", 75_000),
                  ("Marketing Manager", 115_000)],
    "Customer Support": [("Support Agent", 48_000), ("Support Team Lead", 70_000),
                         ("Customer Success Manager", 85_000)],
    "Finance": [("Accountant", 72_000), ("Financial Analyst", 90_000), ("Finance Manager", 130_000)],
    "HR": [("HR Generalist", 68_000), ("Recruiter", 72_000), ("HR Manager", 105_000)],
    "Operations": [("Operations Analyst", 70_000), ("Operations Manager", 110_000),
                   ("Office Administrator", 45_000)],
}
DEPT_WEIGHTS = {"Engineering": 34, "Product": 8, "Sales": 17, "Marketing": 7,
                "Customer Support": 15, "Finance": 6, "HR": 4, "Operations": 9}
# country -> (weight, pay level relative to US)
COUNTRY_PROFILE = {
    "United States": (24, 1.00), "India": (20, 0.30), "United Kingdom": (9, 0.78),
    "Germany": (8, 0.80), "France": (5, 0.72), "Canada": (6, 0.85), "Australia": (4, 0.88),
    "Singapore": (4, 0.85), "Japan": (4, 0.70), "Brazil": (6, 0.38),
    "Poland": (5, 0.45), "United Arab Emirates": (5, 0.75),
}
TYPES = (("full_time", 88), ("part_time", 5), ("contract", 7))
TYPE_FACTOR = {"full_time": 1.0, "part_time": 0.6, "contract": 1.1}
# Whole-unit rounding granularity so salaries look human (e.g. 2,350,000 INR).
ROUND_TO = {"INR": 10_000, "JPY": 100_000, "BRL": 1_000, "AED": 1_000}


def generate_employees(n: int, seed: int = 42, today: date | None = None) -> list[dict]:
    rng = random.Random(seed)
    today = today or date.today()
    depts, dweights = zip(*DEPT_WEIGHTS.items())
    countries = list(COUNTRY_PROFILE)
    cweights = [COUNTRY_PROFILE[c][0] for c in countries]
    types, tweights = zip(*TYPES)
    employees = []
    for i in range(1, n + 1):
        dept = rng.choices(depts, dweights)[0]
        title, base = rng.choice(ROLES[dept])
        country = rng.choices(countries, cweights)[0]
        etype = rng.choices(types, tweights)[0]
        currency = COUNTRY_CURRENCY[country]
        tenure_days = int(rng.triangular(30, 365 * 12, 365 * 2))
        # experience nudges pay up to ~+25%, plus individual noise
        experience = 1 + min(tenure_days / (365 * 12), 1) * 0.25
        usd = base * COUNTRY_PROFILE[country][1] * TYPE_FACTOR[etype] * experience
        usd *= rng.uniform(0.88, 1.12)
        step = ROUND_TO.get(currency, 500)
        salary = max(step, round(usd / USD_PER_UNIT[currency] / step) * step)
        first, last = rng.choice(FIRST), rng.choice(LAST)
        employees.append({
            "name": f"{first} {last}",
            "email": f"{first}.{last}.{i}@acme.com".lower(),   # id suffix guarantees uniqueness
            "job_title": title, "department": dept, "country": country,
            "employment_type": etype, "salary": int(salary), "currency": currency,
            "hire_date": (today - timedelta(days=tenure_days)).isoformat(),
        })
    return employees


def seed(conn, n: int = 10_000, seed_value: int = 42, reset: bool = False) -> int:
    existing = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    if existing and not reset:
        raise SystemExit(f"Database already has {existing} employees. Use --reset to replace.")
    employees = generate_employees(n, seed_value)
    with conn:  # one transaction: all-or-nothing, and fast
        if reset:
            conn.execute("DELETE FROM employees")
        conn.executemany(
            "INSERT INTO employees (id,name,email,job_title,department,country,"
            "employment_type,salary,currency,hire_date) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            [(i, e["name"], e["email"], e["job_title"], e["department"], e["country"],
              e["employment_type"], e["salary"], e["currency"], e["hire_date"])
             for i, e in enumerate(employees, start=1)],
        )
        conn.executemany(
            "INSERT INTO salary_history(employee_id,salary,currency,effective_date,note) "
            "VALUES (?,?,?,?,?)",
            [(i, e["salary"], e["currency"], e["hire_date"], "Starting salary")
             for i, e in enumerate(employees, start=1)],
        )
    return len(employees)


if __name__ == "__main__":
    import os
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-n", type=int, default=10_000, help="number of employees")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    path = os.environ.get("DATABASE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "salary.db"))
    conn = db.connect(path)
    db.init_schema(conn)
    count = seed(conn, args.n, args.seed, args.reset)
    print(f"Seeded {count} employees into {path}")
