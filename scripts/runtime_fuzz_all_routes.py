"""Runtime Fuzzing Audit across all VERA API routes."""

import json
import httpx

BASE_URL = "http://localhost:8000"

routes_to_test = [
    # (method, path, valid_body, headers)
    ("GET", "/health", None, {}),
    ("GET", "/api/v1/health", None, {}),
    ("POST", "/api/v1/investigations", {"title": "Fuzz Test Investigation", "target_entity_name": "FuzzCo"}, {"Content-Type": "application/json"}),
    ("GET", "/api/v1/investigations", None, {}),
    ("POST", "/api/v1/uploads/presigned-url", {"filename": "evidence.png", "mime_type": "image/png", "size_bytes": 1024}, {"Content-Type": "application/json"}),
    ("POST", "/api/v1/privacy/consent", {"user_id": "usr_fuzz_1", "consent_type": "third_party_transcription", "consented": True}, {"Content-Type": "application/json"}),
    ("POST", "/api/v1/privacy/delete-data", {"user_id": "usr_fuzz_1"}, {"Content-Type": "application/json"}),
    ("POST", "/api/v1/deepfake/verify", {"media_type": "VIDEO", "content_payload": "mock_base64_data"}, {"Content-Type": "application/json"}),
]

results = []

def run_fuzz():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    
    # First create one investigation to test sub-routes
    inv_res = client.post("/api/v1/investigations", json={"title": "Fuzz Base", "target_entity_name": "Target"}, headers={"Content-Type": "application/json"})
    inv_id = "inv_default"
    if inv_res.status_code in (200, 201):
        inv_id = inv_res.json().get("id", inv_id)

    sub_routes = [
        ("GET", f"/api/v1/investigations/{inv_id}", None, {}),
        ("POST", f"/api/v1/investigations/{inv_id}/inputs", {"type": "TEXT", "value": "Guaranteed 100% returns"}, {"Content-Type": "application/json"}),
        ("POST", f"/api/v1/investigations/{inv_id}/analyze", {"analyzer_subset": ["engine.message.heuristics"]}, {"Content-Type": "application/json"}),
        ("GET", f"/api/v1/investigations/{inv_id}/report", None, {}),
        ("GET", f"/api/v1/investigations/{inv_id}/evidence", None, {}),
        ("GET", f"/api/v1/investigations/{inv_id}/audit-log", None, {}),
    ]

    all_routes = routes_to_test + sub_routes

    print(f"Auditing {len(all_routes)} API endpoints under 5 payload variations...")

    for method, path, valid_body, headers in all_routes:
        variations = []
        if method == "GET":
            variations.append(("valid", None, headers))
            variations.append(("oversized_query", None, {**headers, "X-Custom": "A" * 5000}))
        else:
            # 1. Valid
            variations.append(("valid", valid_body, headers))
            # 2. Empty
            variations.append(("empty", {}, headers))
            # 3. Invalid types
            variations.append(("invalid_types", {k: 12345678 for k in (valid_body or {})}, headers))
            # 4. Oversized
            oversized = {k: ("OVERSIZED_" * 500) if isinstance(v, str) else v for k, v in (valid_body or {}).items()}
            variations.append(("oversized", oversized, headers))
            # 5. Malformed string payload
            variations.append(("malformed_nulls", {k: "\x00\x01\x02\xff" for k in (valid_body or {})}, headers))

        for var_name, body, h in variations:
            try:
                if method == "GET":
                    resp = client.get(path, headers=h)
                else:
                    resp = client.post(path, json=body, headers=h)
                status_code = resp.status_code
                is_500 = status_code >= 500
                results.append({
                    "method": method,
                    "path": path,
                    "variation": var_name,
                    "status_code": status_code,
                    "is_server_error": is_500,
                    "body_snippet": resp.text[:120],
                })
                if is_500:
                    print(f"[FAIL 500] {method} {path} [{var_name}]: {status_code} - {resp.text[:120]}")
            except Exception as e:
                results.append({
                    "method": method,
                    "path": path,
                    "variation": var_name,
                    "status_code": 0,
                    "is_server_error": True,
                    "error": str(e),
                })
                print(f"[EXCEPTION] {method} {path} [{var_name}]: {e}")

    total_calls = len(results)
    server_errors = [r for r in results if r["is_server_error"]]
    print(f"\nFuzzing Complete: {total_calls} calls executed.")
    print(f"500 Internal Server Errors / Exceptions: {len(server_errors)}")

    with open("eval/results/api_fuzz_report.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2)

if __name__ == "__main__":
    run_fuzz()
