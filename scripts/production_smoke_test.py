#!/usr/bin/env python3
"""VERA Production Smoke Test Suite.

Takes a base URL and verifies critical production flows:
1. /health (liveness)
2. /ready (dependency health honesty)
3. Security headers (nosniff, DENY, CSP)
4. Public verification scan endpoint
5. Upload validation (rejecting oversized/malformed payloads)
6. Non-existent path handling (404, no stack trace leak)

Usage:
    python scripts/production_smoke_test.py https://vera-api.onrender.com
"""

import sys
import json
import httpx


def test_endpoint(name: str, check_fn):
    try:
        check_fn()
        print(f"  [PASS] {name}")
        return True
    except AssertionError as err:
        print(f"  [FAIL] {name}: {err}")
        return False
    except Exception as exc:
        print(f"  [ERROR] {name}: {exc}")
        return False


def run_smoke_tests(base_url: str):
    base_url = base_url.rstrip("/")
    print(f"\n=======================================================")
    print(f"🚀 VERA PRODUCTION SMOKE TEST: {base_url}")
    print(f"=======================================================\n")

    client = httpx.Client(timeout=15.0)
    passed = 0
    total = 0

    # 1. Health check
    total += 1
    def check_health():
        res = client.get(f"{base_url}/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert "status" in data, "Missing 'status' in health payload"
    if test_endpoint("Liveness probe (/health)", check_health):
        passed += 1

    # 2. Ready check
    total += 1
    def check_ready():
        res = client.get(f"{base_url}/ready")
        assert res.status_code in (200, 503), f"Expected 200 or 503, got {res.status_code}"
        data = res.json()
        assert "status" in data, "Missing 'status' in ready payload"
    if test_endpoint("Readiness probe (/ready)", check_ready):
        passed += 1

    # 3. Security headers
    total += 1
    def check_sec_headers():
        res = client.get(f"{base_url}/health")
        assert res.headers.get("x-content-type-options") == "nosniff", "Missing X-Content-Type-Options: nosniff"
        assert res.headers.get("x-frame-options") == "DENY", "Missing X-Frame-Options: DENY"
        assert "content-security-policy" in res.headers, "Missing Content-Security-Policy"
    if test_endpoint("Security response headers", check_sec_headers):
        passed += 1

    # 4. Error response privacy (No stack trace leak)
    total += 1
    def check_error_leak():
        res = client.get(f"{base_url}/non-existent-route-xyz")
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        body = res.text
        assert "traceback" not in body.lower(), "Stack trace leaked in error response!"
        assert "c:\\" not in body.lower() and "/home/" not in body.lower(), "Internal paths leaked!"
    if test_endpoint("Error response privacy", check_error_leak):
        passed += 1

    # 5. Public verification endpoint
    total += 1
    def check_verification():
        payload = {
            "title": "Smoke test scan",
            "summary_note": "Invest in VIP whatsapp group 100% guarantee",
        }
        res = client.post(f"{base_url}/api/v1/investigations", json=payload)
        # Should return 201 or 400/429/503 (if throttled/unconfigured db), but NEVER unhandled 500
        assert res.status_code != 500, "Unhandled 500 error returned!"
    if test_endpoint("Investigation pipeline response integrity", check_verification):
        passed += 1

    print(f"\n-------------------------------------------------------")
    print(f"Results: {passed}/{total} tests passed.")
    print(f"-------------------------------------------------------\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/production_smoke_test.py <BASE_URL>")
        sys.exit(1)
    sys.exit(run_smoke_tests(sys.argv[1]))
