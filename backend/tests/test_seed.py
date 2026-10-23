import unittest
from datetime import date

from seed import generate_employees, seed
from app import db
from app.validation import validate_employee
from tests.helpers import ApiTestCase

TODAY = date(2026, 10, 23)


class GenerateTests(unittest.TestCase):
    def test_same_seed_gives_identical_data(self):
        self.assertEqual(generate_employees(200, 1, TODAY), generate_employees(200, 1, TODAY))

    def test_different_seed_differs(self):
        self.assertNotEqual(generate_employees(50, 1, TODAY), generate_employees(50, 2, TODAY))

    def test_count_and_unique_emails(self):
        emps = generate_employees(2000, 3, TODAY)
        self.assertEqual(len(emps), 2000)
        self.assertEqual(len({e["email"] for e in emps}), 2000)

    def test_every_generated_row_passes_the_api_validation(self):
        for e in generate_employees(500, 5, TODAY):
            cleaned = validate_employee({k: v for k, v in e.items() if k != "currency"}, today=TODAY)
            self.assertEqual(cleaned["currency"], e["currency"])


class SeedLoadTests(ApiTestCase):
    def test_seed_loads_rows_history_and_refuses_second_run(self):
        conn = db.connect(self.path)
        self.assertEqual(seed(conn, 300), 300)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM salary_history").fetchone()[0], 300)
        with self.assertRaises(SystemExit):
            seed(conn, 10)
        self.assertEqual(seed(conn, 50, reset=True), 50)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0], 50)
        conn.close()
        self.assertEqual(self.client.get("/api/summary").get_json()["headcount"], 50)


if __name__ == "__main__":
    unittest.main()
