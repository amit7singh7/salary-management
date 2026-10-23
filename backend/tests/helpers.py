import os
import tempfile
import unittest

from app import create_app


def employee(**overrides):
    base = {
        "name": "Asha Rao", "email": "asha@acme.com", "job_title": "Software Engineer",
        "department": "Engineering", "country": "India", "employment_type": "full_time",
        "salary": 2_400_000, "hire_date": "2022-04-01",
    }
    base.update(overrides)
    return base


class ApiTestCase(unittest.TestCase):
    """Each test gets a fresh temp SQLite file: isolated, fast, deterministic."""

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app({"DATABASE": self.path, "TESTING": True})
        self.client = self.app.test_client()

    def tearDown(self):
        for suffix in ("", "-wal", "-shm"):
            try:
                os.remove(self.path + suffix)
            except FileNotFoundError:
                pass

    def create(self, **overrides):
        res = self.client.post("/api/employees", json=employee(**overrides))
        self.assertEqual(res.status_code, 201, res.get_json())
        return res.get_json()
