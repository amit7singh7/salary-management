"""Latency check against a seeded database.

    DATABASE=/tmp/perf.db python seed.py && DATABASE=/tmp/perf.db python benchmark.py
"""
import statistics
import time

from app import create_app

ENDPOINTS = {
    "list page 1": "/api/employees",
    "list sort by salary desc": "/api/employees?sort=salary&order=desc",
    "list deep page (400)": "/api/employees?page=400",
    "search q=patel": "/api/employees?q=patel",
    "filter country+department": "/api/employees?country=India&department=Engineering",
    "insights by country": "/api/insights?group_by=country",
    "insights by job_title": "/api/insights?group_by=job_title",
    "distribution": "/api/insights/distribution",
    "summary": "/api/summary",
}

if __name__ == "__main__":
    client = create_app().test_client()
    for label, url in ENDPOINTS.items():
        client.get(url)  # warm-up
        samples = []
        for _ in range(20):
            start = time.perf_counter()
            assert client.get(url).status_code == 200
            samples.append((time.perf_counter() - start) * 1000)
        print(f"{label:30s} median {statistics.median(samples):6.1f} ms   max {max(samples):6.1f} ms")
