"""Locust Load Test Script for VERA Backend.

Run locally:
    locust -f tests/load/locustfile.py --host http://localhost:8000 --headless -u 50 -r 10 --run-time 1m
"""

import uuid
from locust import HttpUser, task, between


class VERAUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def test_health(self):
        """Simulate cheap read probes."""
        self.client.get("/health", name="/health")

    @task(1)
    def test_public_scan(self):
        """Simulate public retail user scanning evidence text."""
        payload = {
            "evidence_type": "text",
            "content": "Guaranteed 100% daily profit on Telegram VIP group. Hurry up!",
        }
        headers = {
            "X-Request-ID": f"locust-{uuid.uuid4().hex[:8]}",
            "Content-Type": "application/json",
        }
        with self.client.post("/api/v1/investigations/verify-evidence", json=payload, headers=headers, catch_response=True) as response:
            if response.status_code in (200, 429, 503):
                # Expected operational states under burst traffic
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
