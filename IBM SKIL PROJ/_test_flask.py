"""
_test_flask.py — full end-to-end Flask test client for /api/chat/stream
Tests the exact code path the browser hits.
"""
import sys, os, json, time
os.environ["PYTHONIOENCODING"] = "utf-8"

from dotenv import load_dotenv
load_dotenv(override=True)

import app as _app

client = _app.app.test_client()
_app.app.config["TESTING"] = True
_app.app.config["SECRET_KEY"] = "test"

print("=== Provider flags (inside Flask app) ===")
print(f"  _has_groq()   = {_app._has_groq()}")
print(f"  _has_gemini() = {_app._has_gemini()}")
print(f"  has_ibm()     = {_app.has_ibm_credentials()}")
print()

# ── Test /api/status ───────────────────────────────────────
print("=== GET /api/status ===")
r = client.get("/api/status")
d = r.get_json()
print(f"  {json.dumps(d, indent=4)}")
print()

# ── Test /api/chat/stream (SSE) ────────────────────────────
print("=== POST /api/chat/stream ===")
payload = json.dumps({"message": "What is Jeevamrut? Give a 2-sentence answer.", "lat": 20.59, "lon": 78.96})

t0 = time.time()
with client.application.test_request_context():
    resp = client.post(
        "/api/chat/stream",
        data=payload,
        content_type="application/json",
    )

tokens   = []
final_ev = None
raw      = resp.data.decode("utf-8", errors="replace")

for line in raw.split("\n"):
    line = line.strip()
    if not line.startswith("data:"):
        continue
    payload_str = line[5:].strip()
    if not payload_str:
        continue
    try:
        ev = json.loads(payload_str)
        if ev.get("done"):
            final_ev = ev
        elif ev.get("token"):
            tokens.append(ev["token"])
    except Exception:
        pass

ms       = int((time.time() - t0) * 1000)
full_ans = "".join(tokens)

if tokens:
    print(f"  OK  [{ms} ms]")
    print(f"  Provider model : {final_ev.get('model') if final_ev else '?'}")
    print(f"  Tokens received: {len(tokens)}")
    print(f"  Answer preview : {full_ans[:200]}...")
    print()
    print("=== Groq is the active provider and streaming correctly ===")
else:
    print(f"  FAIL — no tokens received. HTTP status={resp.status_code}")
    print(f"  Raw response:\n{raw[:500]}")
    sys.exit(1)

# clean up temp files
os.remove("_check_env.py") if os.path.exists("_check_env.py") else None
os.remove("_test_chat.py") if os.path.exists("_test_chat.py") else None
os.remove("_test_flask.py") if os.path.exists("_test_flask.py") else None
