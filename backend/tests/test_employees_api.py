from tests.helpers import ApiTestCase, employee


class CrudTests(ApiTestCase):
    def test_create_returns_employee_with_usd_value_and_currency(self):
        emp = self.create()
        self.assertEqual(emp["currency"], "INR")
        self.assertEqual(emp["salary_usd"], 28_800)  # 2.4M * 0.012

    def test_create_writes_starting_salary_history(self):
        emp = self.create()
        hist = self.client.get(f"/api/employees/{emp['id']}").get_json()["history"]
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]["note"], "Starting salary")
        self.assertEqual(hist[0]["effective_date"], "2022-04-01")

    def test_validation_errors_return_422_with_field_messages(self):
        res = self.client.post("/api/employees", json=employee(salary=-1, email="bad"))
        self.assertEqual(res.status_code, 422)
        fields = res.get_json()["fields"]
        self.assertIn("salary", fields)
        self.assertIn("email", fields)

    def test_invalid_json_body_is_422_not_500(self):
        res = self.client.post("/api/employees", data="nope", content_type="application/json")
        self.assertEqual(res.status_code, 422)

    def test_duplicate_email_rejected_case_insensitively(self):
        self.create()
        res = self.client.post("/api/employees", json=employee(email="ASHA@acme.com"))
        self.assertEqual(res.status_code, 422)
        self.assertIn("email", res.get_json()["fields"])

    def test_update_salary_appends_history(self):
        emp = self.create()
        res = self.client.put(f"/api/employees/{emp['id']}",
                              json=employee(salary=2_800_000))
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body["salary"], 2_800_000)
        self.assertEqual(len(body["history"]), 2)
        self.assertIn("2400000", body["history"][0]["note"])

    def test_update_without_salary_change_adds_no_history(self):
        emp = self.create()
        body = self.client.put(f"/api/employees/{emp['id']}",
                               json=employee(job_title="Senior Engineer")).get_json()
        self.assertEqual(body["job_title"], "Senior Engineer")
        self.assertEqual(len(body["history"]), 1)

    def test_update_can_keep_own_email_but_not_take_anothers(self):
        a = self.create()
        b = self.create(email="b@acme.com", name="B")
        ok = self.client.put(f"/api/employees/{a['id']}", json=employee())
        self.assertEqual(ok.status_code, 200)
        clash = self.client.put(f"/api/employees/{b['id']}", json=employee(email="asha@acme.com"))
        self.assertEqual(clash.status_code, 422)

    def test_country_change_changes_currency_and_records_history(self):
        emp = self.create()
        body = self.client.put(f"/api/employees/{emp['id']}",
                               json=employee(country="Germany", salary=2_400_000)).get_json()
        self.assertEqual(body["currency"], "EUR")
        self.assertEqual(len(body["history"]), 2)

    def test_get_update_delete_unknown_id_404(self):
        self.assertEqual(self.client.get("/api/employees/999").status_code, 404)
        self.assertEqual(self.client.put("/api/employees/999", json=employee()).status_code, 404)
        self.assertEqual(self.client.delete("/api/employees/999").status_code, 404)

    def test_delete_removes_employee_and_history(self):
        emp = self.create()
        self.assertEqual(self.client.delete(f"/api/employees/{emp['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/employees/{emp['id']}").status_code, 404)
        with self.app.app_context():
            from app.db import get_db
            n = get_db().execute("SELECT COUNT(*) FROM salary_history").fetchone()[0]
        self.assertEqual(n, 0)


class ListTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.create(name="Zed", email="z@a.com", country="United States", department="Sales",
                    job_title="Account Executive", salary=100_000)
        self.create(name="amy", email="amy@a.com", country="United States", department="Engineering",
                    job_title="Software Engineer", salary=150_000)
        self.create(name="Bob", email="bob@a.com", country="India", department="Engineering",
                    job_title="Software Engineer", salary=3_000_000, employment_type="contract")

    def names(self, qs=""):
        return [e["name"] for e in self.client.get("/api/employees" + qs).get_json()["items"]]

    def test_default_sort_is_case_insensitive_name(self):
        self.assertEqual(self.names(), ["amy", "Bob", "Zed"])

    def test_filters_combine_with_and(self):
        self.assertEqual(self.names("?country=United States&department=Engineering"), ["amy"])
        self.assertEqual(self.names("?employment_type=contract"), ["Bob"])

    def test_search_matches_name_or_email(self):
        self.assertEqual(self.names("?q=AMY"), ["amy"])
        self.assertEqual(self.names("?q=bob@"), ["Bob"])

    def test_search_treats_like_wildcards_literally(self):
        self.assertEqual(self.names("?q=%"), [])

    def test_sort_by_salary_uses_usd_so_countries_compare(self):
        # Bob: 3,000,000 INR = $36,000 -> lowest despite the biggest raw number
        self.assertEqual(self.names("?sort=salary&order=asc"), ["Bob", "Zed", "amy"])
        self.assertEqual(self.names("?sort=salary&order=desc"), ["amy", "Zed", "Bob"])

    def test_unknown_sort_column_falls_back_safely(self):
        self.assertEqual(self.names("?sort=id;DROP TABLE employees"), ["amy", "Bob", "Zed"])

    def test_pagination_and_total(self):
        body = self.client.get("/api/employees?page_size=2&page=2").get_json()
        self.assertEqual(body["total"], 3)
        self.assertEqual([e["name"] for e in body["items"]], ["Zed"])

    def test_page_size_is_capped(self):
        body = self.client.get("/api/employees?page_size=100000").get_json()
        self.assertEqual(body["page_size"], 100)

    def test_meta_lists_filter_options(self):
        meta = self.client.get("/api/meta").get_json()
        self.assertEqual(meta["departments"], ["Engineering", "Sales"])
        self.assertIn({"name": "India", "currency": "INR"}, meta["countries"])

    def test_search_finds_underscore_in_email(self):
        self.create(name="Under", email="john_doe@a.com")
        self.create(name="Other", email="johnXdoe@a.com")
        self.assertEqual(self.names("?q=john_doe"), ["Under"])
