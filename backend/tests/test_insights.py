import unittest

from app.insights import percentile, summarize
from tests.helpers import ApiTestCase


class StatsTests(unittest.TestCase):
    def test_percentile_interpolates(self):
        vals = [10, 20, 30, 40]
        self.assertEqual(percentile(vals, 0), 10)
        self.assertEqual(percentile(vals, 50), 25)   # between 20 and 30
        self.assertEqual(percentile(vals, 100), 40)
        self.assertEqual(percentile(vals, 25), 17.5)

    def test_percentile_single_value(self):
        self.assertEqual(percentile([7], 90), 7)

    def test_percentile_empty_raises(self):
        with self.assertRaises(ValueError):
            percentile([], 50)

    def test_summarize_does_not_depend_on_input_order(self):
        a = summarize([30, 10, 20])
        b = summarize([10, 20, 30])
        self.assertEqual(a, b)
        self.assertEqual((a["min"], a["median"], a["max"], a["average"], a["headcount"]),
                         (10, 20, 30, 20, 3))


class InsightsApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        us = dict(country="United States")
        self.create(email="1@a.com", salary=100_000, department="Engineering", **us)
        self.create(email="2@a.com", salary=200_000, department="Engineering", **us)
        self.create(email="3@a.com", salary=60_000, department="Sales", **us)
        # 5,000,000 INR = $60,000
        self.create(email="4@a.com", salary=5_000_000, department="Sales", country="India")

    def groups(self, qs):
        body = self.client.get("/api/insights" + qs).get_json()
        return {g["group"]: g for g in body["groups"]}

    def test_group_by_country_has_local_and_usd_stats(self):
        g = self.groups("?group_by=country")
        self.assertEqual(g["United States"]["headcount"], 3)
        self.assertEqual(g["United States"]["median"], 100_000)
        self.assertEqual(g["India"]["median"], 60_000)            # USD-normalised
        self.assertEqual(g["India"]["local"]["median"], 5_000_000)  # local currency
        self.assertEqual(g["India"]["currency"], "INR")

    def test_group_spanning_currencies_has_no_local_stats(self):
        g = self.groups("?group_by=department")
        self.assertEqual(g["Sales"]["headcount"], 2)
        self.assertNotIn("local", g["Sales"])
        self.assertEqual(g["Sales"]["average"], 60_000)

    def test_filters_apply_before_grouping(self):
        g = self.groups("?group_by=department&country=United States")
        self.assertEqual(g["Engineering"]["headcount"], 2)
        self.assertEqual(g["Sales"]["headcount"], 1)
        self.assertEqual(g["Sales"]["currency"], "USD")

    def test_groups_sorted_by_median_desc(self):
        body = self.client.get("/api/insights?group_by=department").get_json()
        medians = [g["median"] for g in body["groups"]]
        self.assertEqual(medians, sorted(medians, reverse=True))

    def test_invalid_group_by_is_400(self):
        res = self.client.get("/api/insights?group_by=salary;--")
        self.assertEqual(res.status_code, 400)

    def test_empty_result_is_empty_list(self):
        body = self.client.get("/api/insights?country=Japan").get_json()
        self.assertEqual(body["groups"], [])

    def test_summary(self):
        s = self.client.get("/api/summary").get_json()
        self.assertEqual(s["headcount"], 4)
        self.assertEqual(s["total_payroll_usd"], 420_000)
        self.assertEqual(s["countries"], 2)

    def test_summary_of_empty_filter(self):
        s = self.client.get("/api/summary?country=Japan").get_json()
        self.assertEqual(s["headcount"], 0)

    def test_distribution_buckets(self):
        body = self.client.get("/api/insights/distribution").get_json()
        by_from = {b["from"]: b["count"] for b in body["buckets"]}
        self.assertEqual(by_from[50_000], 2)    # $60k x2 -> 50-75k
        self.assertEqual(by_from[100_000], 1)   # $100k
        self.assertEqual(by_from[200_000], 1)   # $200k
        self.assertEqual(sum(by_from.values()), 4)
        self.assertIsNone(body["buckets"][-1]["to"])

    def test_distribution_top_bucket_is_open_ended(self):
        self.create(email="rich@a.com", salary=900_000, country="United States")
        body = self.client.get("/api/insights/distribution").get_json()
        self.assertEqual(body["buckets"][-1]["count"], 1)


if __name__ == "__main__":
    unittest.main()
