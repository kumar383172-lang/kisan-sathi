"""
check_apis.py — Test all configured LLM + service API connections
Run: python check_apis.py
"""
import os, sys, json, time, requests
from dotenv import load_dotenv

load_dotenv()

SEP   = "─" * 56
OK    = "✅"
FAIL  = "❌"
SKIP  = "⏭️ "
WARN  = "⚠️ "

results = []

def header(title):
    print(f"\n{SEP}\n  {title}\n{SEP}")

def log(icon, label, msg=""):
    line = f"  {icon}  {label}"
    if msg:
        line += f"  →  {msg}"
    print(line)
    results.append((icon, label, msg))


# ── 1. Groq ──────────────────────────────────────────────────
header("1 · Groq  (free tier · Llama 3.3 70B)")
groq_key = os.getenv("GROQ_API_KEY", "").strip()
if not groq_key or groq_key == "your_groq_api_key_here":
    log(SKIP, "GROQ_API_KEY not set — skipping")
else:
    log(OK, f"GROQ_API_KEY found  ({groq_key[:8]}…{groq_key[-4:]})")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    try:
        t0   = time.time()
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model":      model,
                "messages":   [{"role": "user", "content": "Say exactly: GROQ_OK"}],
                "max_tokens": 10,
                "stream":     False,
            },
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            timeout=15,
        )
        ms = int((time.time() - t0) * 1000)
        if resp.status_code == 200:
            reply = resp.json()["choices"][0]["message"]["content"].strip()
            log(OK, f"Chat API  [{ms} ms]", f'model={model}  reply="{reply}"')
        else:
            log(FAIL, f"HTTP {resp.status_code}", resp.text[:200])
    except Exception as e:
        log(FAIL, "Connection error", str(e))


# ── 2. Google Gemini ─────────────────────────────────────────
header("2 · Google Gemini  (free tier · 1.5 Flash)")
gem_key = os.getenv("GEMINI_API_KEY", "").strip()
if not gem_key or gem_key == "your_gemini_api_key_here":
    log(SKIP, "GEMINI_API_KEY not set — skipping")
else:
    log(OK, f"GEMINI_API_KEY found  ({gem_key[:8]}…{gem_key[-4:]})")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    try:
        t0   = time.time()
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gem_key}",
            json={"contents": [{"role": "user", "parts": [{"text": "Say exactly: GEMINI_OK"}]}],
                  "generationConfig": {"maxOutputTokens": 10}},
            timeout=15,
        )
        ms = int((time.time() - t0) * 1000)
        if resp.status_code == 200:
            reply = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            log(OK, f"generateContent  [{ms} ms]", f'model={model}  reply="{reply}"')
        else:
            log(FAIL, f"HTTP {resp.status_code}", resp.text[:200])
    except Exception as e:
        log(FAIL, "Connection error", str(e))


# ── 3. IBM Watsonx ───────────────────────────────────────────
header("3 · IBM Watsonx  (optional)")
ibm_key = os.getenv("IBM_API_KEY", "").strip()
ibm_pid = os.getenv("IBM_PROJECT_ID", "").strip()
if not ibm_key or ibm_key == "your_ibm_cloud_api_key_here":
    log(SKIP, "IBM_API_KEY not set — skipping")
else:
    log(OK, f"IBM_API_KEY found  ({ibm_key[:6]}…)")
    try:
        t0   = time.time()
        resp = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": ibm_key},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        ms = int((time.time() - t0) * 1000)
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            log(OK, f"IAM token obtained  [{ms} ms]", f"token={token[:16]}…")
            if ibm_pid and ibm_pid != "your_watsonx_project_id_here":
                log(OK, f"IBM_PROJECT_ID found  ({ibm_pid[:8]}…)")
            else:
                log(WARN, "IBM_PROJECT_ID not set — Watsonx calls will fail")
        else:
            log(FAIL, f"IAM HTTP {resp.status_code}", resp.text[:200])
    except Exception as e:
        log(FAIL, "IAM connection error", str(e))


# ── 4. Open-Meteo (no key) ───────────────────────────────────
header("4 · Open-Meteo weather  (no key required)")
try:
    t0   = time.time()
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": 20.59, "longitude": 78.96, "current": "temperature_2m"},
        timeout=10,
    )
    ms = int((time.time() - t0) * 1000)
    if resp.status_code == 200:
        temp = resp.json()["current"]["temperature_2m"]
        log(OK, f"Open-Meteo  [{ms} ms]", f"temperature={temp}°C")
    else:
        log(FAIL, f"HTTP {resp.status_code}", resp.text[:100])
except Exception as e:
    log(FAIL, "Connection error", str(e))


# ── Summary ──────────────────────────────────────────────────
header("SUMMARY")
ok_count   = sum(1 for r in results if r[0] == OK)
fail_count = sum(1 for r in results if r[0] == FAIL)
skip_count = sum(1 for r in results if r[0] == SKIP)

active = (
    "Groq"         if os.getenv("GROQ_API_KEY","").strip() not in ("","your_groq_api_key_here") else
    "Google Gemini" if os.getenv("GEMINI_API_KEY","").strip() not in ("","your_gemini_api_key_here") else
    "IBM Watsonx"  if os.getenv("IBM_API_KEY","").strip() not in ("","your_ibm_cloud_api_key_here") else
    "NONE — only built-in fallback will work"
)

print(f"  {OK}  Passed : {ok_count}")
print(f"  {FAIL}  Failed : {fail_count}")
print(f"  {SKIP}  Skipped: {skip_count}")
print(f"\n  Active LLM provider  →  {active}")
print()

if fail_count:
    print("  Fix failed connections before starting the app.\n")
    sys.exit(1)
else:
    print("  All checked connections are working. Run: python app.py\n")
