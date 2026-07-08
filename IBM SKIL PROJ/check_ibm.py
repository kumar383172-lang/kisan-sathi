"""
check_ibm.py
Diagnostic script -- run with:  python check_ibm.py
Tests IBM credentials step by step without printing secrets to screen.
"""
import os, sys, io, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from dotenv import load_dotenv

load_dotenv()

API_KEY    = os.getenv("IBM_API_KEY", "").strip()
PROJECT_ID = os.getenv("IBM_PROJECT_ID", "").strip()
WX_URL     = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com").strip()
MODEL_ID   = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2").strip()

SEP = "-" * 62

def mask(s):
    if not s: return "(empty)"
    if len(s) < 12: return "***"
    return s[:6] + "..." + s[-4:]

print(SEP)
print("  IBM Watsonx Credential Diagnostic")
print(SEP)
print(f"  IBM_API_KEY      : {mask(API_KEY)}")
print(f"  IBM_PROJECT_ID   : {mask(PROJECT_ID)}")
print(f"  IBM_WATSONX_URL  : {WX_URL}")
print(f"  WATSONX_MODEL_ID : {MODEL_ID}")
print(SEP)

# STEP 1 -- check placeholders
errors = []
if not API_KEY or API_KEY in ("your_ibm_cloud_api_key_here", "your_key"):
    errors.append("FAIL  IBM_API_KEY is empty or still a placeholder")
if not PROJECT_ID or PROJECT_ID in ("your_watsonx_project_id_here", "your_project_id"):
    errors.append("FAIL  IBM_PROJECT_ID is empty or still a placeholder")

if errors:
    for e in errors:
        print(e)
    print()
    print(">>>  How to fix:")
    print("     1. Go to https://cloud.ibm.com")
    print("     2. Manage > Access (IAM) > API keys > Create  (copy the key)")
    print("     3. Open Watsonx.ai > your project > Manage tab > copy Project ID")
    print("     4. Paste both values into your .env file")
    sys.exit(1)

print("STEP 1 OK -- credentials are non-empty\n")

# STEP 2 -- IAM token exchange
print("STEP 2 -- testing IBM IAM token ...")
try:
    r = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": API_KEY},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if r.status_code == 400:
        j = r.json()
        print(f"FAIL  IAM 400: {j.get('errorMessage', r.text[:200])}")
        print("      The API key is malformed or invalid. Re-create it on IBM Cloud.")
        sys.exit(1)
    elif r.status_code == 401:
        print("FAIL  IAM 401 Unauthorized -- API key is expired or revoked.")
        print("      Regenerate: cloud.ibm.com > Manage > Access (IAM) > API keys")
        sys.exit(1)
    r.raise_for_status()
    token = r.json().get("access_token", "")
    if not token:
        print("FAIL  No access_token in IAM response")
        sys.exit(1)
    print(f"STEP 2 OK -- IAM token received (prefix: {token[:14]}...)\n")
except requests.exceptions.ConnectionError:
    print("FAIL  Cannot reach iam.cloud.ibm.com -- check internet connection.")
    sys.exit(1)
except Exception as e:
    print(f"FAIL  IAM error: {e}")
    sys.exit(1)

# STEP 3 -- Watsonx generation
print(f"STEP 3 -- testing Watsonx generation endpoint ...")
print(f"         URL   : {WX_URL}")
print(f"         Model : {MODEL_ID}")
endpoint = f"{WX_URL}/ml/v1/text/generation?version=2023-05-29"
payload = {
    "model_id":   MODEL_ID,
    "project_id": PROJECT_ID,
    "input":      "<|system|>\nYou are helpful.\n<|user|>\nSay hello in one sentence.\n<|assistant|>",
    "parameters": {"max_new_tokens": 40, "temperature": 0.3, "stop_sequences": ["<|user|>"]},
}
try:
    r2 = requests.post(
        endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    if r2.status_code == 404:
        print("FAIL  Watsonx 404 -- URL or model_id is wrong.")
        print(f"      URL tried: {endpoint}")
        print(f"      Model tried: {MODEL_ID}")
        print("      Fix: IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com")
        print("      Fix: WATSONX_MODEL_ID=ibm/granite-13b-chat-v2")
        sys.exit(1)
    elif r2.status_code == 403:
        j2 = r2.json()
        print(f"FAIL  Watsonx 403 Forbidden: {j2.get('message', r2.text[:300])}")
        print(f"      Project ID tried: {mask(PROJECT_ID)}")
        print("      Fix: Watsonx.ai > your project > Manage tab > copy the correct Project ID")
        sys.exit(1)
    elif r2.status_code == 422:
        j2 = r2.json()
        print(f"FAIL  Watsonx 422 Unprocessable: {j2}")
        print("      Model not available on your plan.")
        print("      Try: WATSONX_MODEL_ID=ibm/granite-3-8b-instruct")
        sys.exit(1)
    r2.raise_for_status()
    generated = r2.json().get("results", [{}])[0].get("generated_text", "").strip()
    print(f"STEP 3 OK -- model responded: \"{generated}\"\n")
    print(SEP)
    print("  ALL CHECKS PASSED! IBM Watsonx is fully configured.")
    print("  The chatbot will now use real IBM Granite AI responses.")
    print(SEP)
except requests.exceptions.ConnectionError:
    print(f"FAIL  Cannot reach {WX_URL}")
    print("      Fix: IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com")
    sys.exit(1)
except Exception as e:
    print(f"FAIL  Watsonx error: {e}")
    sys.exit(1)
