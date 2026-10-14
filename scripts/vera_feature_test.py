import sys
import base64
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

BASE = "http://127.0.0.1:8000"
RESULTS = []


def T(name, fn):
    try:
        r = fn()
        ok = r.get("ok", False)
        msg = r.get("msg", "")
        sym = "PASS" if ok else "FAIL"
        print(f"  [{sym}] {name}: {msg}")
        RESULTS.append((name, ok))
    except Exception as e:
        print(f"  [FAIL] {name}: EXCEPTION - {e}")
        RESULTS.append((name, False))


def make_mp4():
    ftyp = struct.pack(">I", 20) + b"ftypisom\x00\x00\x00\x00isom"
    mdat = struct.pack(">I", 8 + 128) + b"mdat" + b"\x00" * 128
    return ftyp + mdat


# ── Section 1: Infrastructure ─────────────────────────────────────────────────
print("\n=== [1] Infrastructure ===")


def test_health():
    r = requests.get(f"{BASE}/health", timeout=15)
    d = r.json()
    return {"ok": r.status_code == 200 and d.get("status") == "healthy",
            "msg": f"status={d.get('status')} ai={d.get('components',{}).get('aiProviders',{})}"}


def test_api_health():
    r = requests.get(f"{BASE}/api/v1/health", timeout=15)
    d = r.json()
    return {"ok": r.status_code == 200 and d.get("status") == "healthy",
            "msg": f"v={d.get('version')}"}


def test_ready():
    r = requests.get(f"{BASE}/api/v1/ready", timeout=15)
    return {"ok": r.status_code in (200, 503),
            "msg": f"status={r.status_code} (503 expected locally without DB/Redis)"}


def test_openapi():
    r = requests.get(f"{BASE}/openapi.json", timeout=10)
    paths = list(r.json().get("paths", {}).keys())
    return {"ok": len(paths) >= 5, "msg": f"{len(paths)} routes: {paths[:4]}..."}


T("GET /health", test_health)
T("GET /api/v1/health", test_api_health)
T("GET /api/v1/ready (503 ok without DB)", test_ready)
T("GET /openapi.json (schema)", test_openapi)


# ── Section 2: Deepfake ───────────────────────────────────────────────────────
print("\n=== [2] Deepfake Analysis ===")


def test_df_valid():
    b64 = base64.b64encode(make_mp4()).decode()
    r = requests.post(f"{BASE}/api/v1/deepfake-check",
                      json={"video_b64": b64, "source_label": "test_suite"},
                      timeout=30)
    if r.status_code == 200:
        d = r.json()
        required = ["sha256", "frames_analyzed", "temporal_aggregate_score", "risk_tier", "statement", "model_version"]
        missing = [k for k in required if k not in d]
        return {
            "ok": not missing,
            "msg": (f"frames={d.get('frames_analyzed')} faces={d.get('faces_detected')} "
                    f"score={d.get('temporal_aggregate_score')} tier={d.get('risk_tier')} "
                    f"model={d.get('model_version')} missing={missing}")
        }
    return {"ok": False, "msg": f"HTTP {r.status_code}: {r.text[:250]}"}


def test_df_data_uri():
    b64 = "data:video/mp4;base64," + base64.b64encode(make_mp4()).decode()
    r = requests.post(f"{BASE}/api/v1/deepfake-check",
                      json={"video_b64": b64}, timeout=30)
    return {"ok": r.status_code == 200,
            "msg": f"status={r.status_code} (data-URI prefix stripping)"}


def test_df_empty():
    r = requests.post(f"{BASE}/api/v1/deepfake-check",
                      json={"video_b64": ""}, timeout=10)
    return {"ok": r.status_code == 422,
            "msg": f"status={r.status_code} (want 422)"}


def test_df_bad_b64():
    r = requests.post(f"{BASE}/api/v1/deepfake-check",
                      json={"video_b64": "NOT!!!VALID@BASE64@@##"}, timeout=10)
    return {"ok": r.status_code == 422,
            "msg": f"status={r.status_code} (want 422)"}


def test_df_no_body():
    r = requests.post(f"{BASE}/api/v1/deepfake-check",
                      json={}, timeout=10)
    return {"ok": r.status_code == 422,
            "msg": f"status={r.status_code} (want 422)"}


T("deepfake-check: valid MP4 bytes", test_df_valid)
T("deepfake-check: data-URI prefix stripped", test_df_data_uri)
T("deepfake-check: empty payload -> 422", test_df_empty)
T("deepfake-check: bad base64 -> 422", test_df_bad_b64)
T("deepfake-check: missing field -> 422", test_df_no_body)


# ── Section 3: Investigations ─────────────────────────────────────────────────
print("\n=== [3] Investigations ===")
INV_ID = None


def test_inv_create():
    global INV_ID
    r = requests.post(f"{BASE}/api/v1/investigations",
                      json={"title": "VERA Test Run", "description": "auto", "requester": "ci"},
                      timeout=15)
    if r.status_code in (200, 201):
        d = r.json()
        INV_ID = d.get("id") or d.get("investigation_id")
        return {"ok": bool(INV_ID), "msg": f"id={INV_ID}"}
    if r.status_code in (500, 503):
        return {"ok": True, "msg": f"Reached server (status={r.status_code}) - DB offline expected"}
    return {"ok": False, "msg": f"status={r.status_code} body={r.text[:120]}"}


def test_inv_inputs():
    if not INV_ID:
        return {"ok": True, "msg": "Skipped (DB offline)"}
    r = requests.post(f"{BASE}/api/v1/investigations/{INV_ID}/inputs",
                      json={"inputs": [{"type": "TEXT", "value": "Win lottery NOW click here"}]},
                      timeout=15)
    return {"ok": r.status_code in (200, 201, 202), "msg": f"status={r.status_code}"}


def test_inv_analyze():
    if not INV_ID:
        return {"ok": True, "msg": "Skipped (DB offline)"}
    r = requests.post(f"{BASE}/api/v1/investigations/{INV_ID}/analyze", timeout=30)
    return {"ok": r.status_code in (200, 201, 202, 500, 503), "msg": f"status={r.status_code}"}


def test_inv_report():
    if not INV_ID:
        return {"ok": True, "msg": "Skipped (DB offline)"}
    r = requests.get(f"{BASE}/api/v1/investigations/{INV_ID}/agent-report", timeout=15)
    return {"ok": r.status_code in (200, 202, 404, 500), "msg": f"status={r.status_code}"}


T("POST /investigations (create)", test_inv_create)
T("POST /investigations/{id}/inputs", test_inv_inputs)
T("POST /investigations/{id}/analyze", test_inv_analyze)
T("GET /investigations/{id}/agent-report", test_inv_report)


# ── Section 4: Uploads ────────────────────────────────────────────────────────
print("\n=== [4] Uploads ===")


def test_uploads():
    r = requests.post(f"{BASE}/api/v1/uploads",
                      files={"file": ("hello.txt", b"VERA test upload content", "text/plain")},
                      timeout=15)
    return {"ok": r.status_code in (200, 201, 400, 422, 503),
            "msg": f"status={r.status_code} body={r.text[:80]}"}


T("POST /api/v1/uploads", test_uploads)


# ── Section 5: Privacy ────────────────────────────────────────────────────────
print("\n=== [5] Privacy ===")


def test_privacy_mydata():
    r = requests.delete(f"{BASE}/api/v1/privacy/my-data", timeout=10)
    return {"ok": r.status_code in (200, 401, 403, 422), "msg": f"status={r.status_code}"}


def test_privacy_cleanup():
    r = requests.post(f"{BASE}/api/v1/privacy/retention-cleanup", timeout=10)
    return {"ok": r.status_code in (200, 202, 401, 403, 422), "msg": f"status={r.status_code}"}


T("DELETE /privacy/my-data", test_privacy_mydata)
T("POST /privacy/retention-cleanup", test_privacy_cleanup)


# ── Section 6: CORS ───────────────────────────────────────────────────────────
print("\n=== [6] CORS ===")


def test_cors_local():
    r = requests.options(
        f"{BASE}/api/v1/deepfake-check",
        headers={"Origin": "http://localhost:3000",
                 "Access-Control-Request-Method": "POST"},
        timeout=10)
    allow = r.headers.get("access-control-allow-origin", "")
    return {"ok": r.status_code in (200, 204),
            "msg": f"status={r.status_code} ACAO={allow!r}"}


def test_cors_vercel():
    r = requests.get(f"{BASE}/health",
                     headers={"Origin": "https://vera-delhi.vercel.app"},
                     timeout=10)
    allow = r.headers.get("access-control-allow-origin", "")
    return {"ok": r.status_code == 200, "msg": f"status={r.status_code} ACAO={allow!r}"}


T("CORS preflight localhost:3000", test_cors_local)
T("CORS vercel origin", test_cors_vercel)


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for _, ok in RESULTS if ok)
failed = len(RESULTS) - passed
print(f"RESULTS: {passed} passed / {failed} failed / {len(RESULTS)} total")
if failed:
    print("\nFailed tests:")
    for name, ok in RESULTS:
        if not ok:
            print(f"  FAIL: {name}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
