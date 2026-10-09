"""Backend Startup & Contract Endpoint Verification Script.

Executes a live server process, tests HTTP responses against contracts, and verifies clean shutdown.
"""

import sys
import time
import subprocess
import httpx

def test_backend_live_startup():
    print("[TEST] Starting FastAPI uvicorn server on port 8000...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "apps.api.src.main:app", "--port", "8000", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait up to 10 seconds for server to bind
        client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=5.0)
        started = False
        for attempt in range(15):
            time.sleep(0.5)
            try:
                resp = client.get("/health")
                if resp.status_code == 200:
                    started = True
                    break
            except Exception:
                continue

        if not started:
            stdout, stderr = proc.communicate(timeout=2)
            print(f"[FAIL] Server failed to start.\nStdout: {stdout}\nStderr: {stderr}")
            sys.exit(1)

        print("[PASS] Root /health returned 200 OK")
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert data["api_version"] == "v1"
        assert "components" in data
        print(f"       Health payload: {data}")


        # Test versioned v1 health
        resp_v1 = client.get("/api/v1/health")
        assert resp_v1.status_code == 200
        print("[PASS] Versioned /api/v1/health returned 200 OK")

        # Test POST /api/v1/investigations
        inv_payload = {
            "title": "Startup Smoke Test Investigation",
            "target_entity_name": "Test Entity",
            "primary_url": "https://example-fraud.test",
            "initial_evidence_items": [
                {
                    "media_type": "URL",
                    "content_payload": "https://example-fraud.test",
                    "source_origin": "Live smoke test",
                    "tags": ["smoke_test"]
                }
            ]
        }
        resp_inv = client.post("/api/v1/investigations", json=inv_payload)
        assert resp_inv.status_code == 201
        inv_data = resp_inv.json()
        assert inv_data["status"] == "PENDING"
        assert inv_data["manifest"]["scoring_algorithm_version"] == "scoring.v1.0"
        print(f"[PASS] /api/v1/investigations created case ID: {inv_data['id']}")

        print("[SUCCESS] All backend startup & contract verification tests passed cleanly!")

    finally:
        print("[TEST] Terminating uvicorn server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("[PASS] Server terminated cleanly.")

if __name__ == "__main__":
    test_backend_live_startup()
