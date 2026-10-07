"""Frontend Startup & Rendering Verification Script.

Executes Next.js production server, queries port 3000, validates rendered HTML, and ensures clean shutdown.
"""

import sys
import time
import subprocess
import httpx

def test_frontend_live_startup():
    print("[TEST] Starting Next.js server on port 3000...")
    # Using shell=True on Windows for npm execution
    proc = subprocess.Popen(
        "npm run start --workspace=@vera/web",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        client = httpx.Client(base_url="http://127.0.0.1:3000", timeout=5.0)
        started = False
        for attempt in range(20):
            time.sleep(0.5)
            try:
                resp = client.get("/")
                if resp.status_code == 200:
                    started = True
                    break
            except Exception:
                continue

        if not started:
            print("[FAIL] Next.js server failed to respond within 10s.")
            sys.exit(1)

        print("[PASS] Next.js HTTP GET / responded with 200 OK")
        html_body = resp.text
        assert "VERA" in html_body
        assert "Phase 0" in html_body or "Investigation" in html_body
        print("[PASS] VERA Architecture Dashboard rendered successfully!")
        print("[SUCCESS] Frontend startup test completed cleanly.")

    finally:
        print("[TEST] Terminating Next.js server process tree...")
        # On Windows, kill process tree
        subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, capture_output=True)
        print("[PASS] Frontend server terminated.")

if __name__ == "__main__":
    test_frontend_live_startup()
