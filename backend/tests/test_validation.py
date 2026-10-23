import unittest
from datetime import date

from app.validation import ValidationError, validate_employee

TODAY = date(2026, 10, 23)


def valid(**overrides):
    base = {
        "name": "  Asha   Rao ",
        "email": "Asha.Rao@Acme.com",
        "job_title": "Software Engineer",
        "department": "Engineering",
        "country": "India",
        "employment_type": "full_time",
        "salary": 2_400_000,
        "hire_date": "2022-04-01",
    }
    base.update(overrides)
    return base


class ValidateEmployeeTests(unittest.TestCase):
    def test_valid_payload_is_cleaned_and_currency_derived(self):
        out = validate_employee(valid(), today=TODAY)
        self.assertEqual(out["name"], "Asha Rao")            # whitespace collapsed
        self.assertEqual(out["email"], "asha.rao@acme.com")  # lower-cased
        self.assertEqual(out["currency"], "INR")             # derived, never client-supplied

    def test_client_supplied_currency_is_ignored(self):
        out = validate_employee(valid(currency="USD"), today=TODAY)
        self.assertEqual(out["currency"], "INR")

    def assertFieldError(self, field, **overrides):
        with self.assertRaises(ValidationError) as ctx:
            validate_employee(valid(**overrides), today=TODAY)
        self.assertIn(field, ctx.exception.errors)

    def test_required_text_fields(self):
        for field in ("name", "email", "job_title", "department"):
            self.assertFieldError(field, **{field: "   "})

    def test_bad_email(self):
        self.assertFieldError("email", email="not-an-email")

    def test_unknown_country(self):
        self.assertFieldError("country", country="Atlantis")

    def test_bad_employment_type(self):
        self.assertFieldError("employment_type", employment_type="intern")

    def test_salary_rules(self):
        for bad in (0, -5, "100", True, 1.5, None, 10**12):
            self.assertFieldError("salary", salary=bad)
        self.assertEqual(validate_employee(valid(salary=100.0), today=TODAY)["salary"], 100)

    def test_hire_date_rules(self):
        self.assertFieldError("hire_date", hire_date="01/02/2020")
        self.assertFieldError("hire_date", hire_date="2026-10-24")  # future
        validate_employee(valid(hire_date="2026-10-23"), today=TODAY)  # today is fine

    def test_all_errors_reported_together(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_employee({}, today=TODAY)
        self.assertGreaterEqual(len(ctx.exception.errors), 7)

    def test_non_object_body(self):
        with self.assertRaises(ValidationError):
            validate_employee([], today=TODAY)


if __name__ == "__main__":
    unittest.main()
