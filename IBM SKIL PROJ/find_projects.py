"""
find_projects.py -- lists all Watsonx projects accessible to the current API key
"""
import io, sys, os, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("IBM_API_KEY","").strip()
WX_URL  = os.getenv("IBM_WATSONX_URL","https://us-south.ml.cloud.ibm.com").strip()

# Get IAM token
r = requests.post(
    "https://iam.cloud.ibm.com/identity/token",
    data={"grant_type":"urn:ibm:params:oauth:grant-type:apikey","apikey":API_KEY},
    headers={"Content-Type":"application/x-www-form-urlencoded"},
    timeout=15,
)
r.raise_for_status()
token = r.json()["access_token"]
print("IAM token: OK\n")

# List projects
print("--- Projects accessible to this API key ---")
rp = requests.get(
    "https://api.dataplatform.cloud.ibm.com/v2/projects?limit=10",
    headers={"Authorization": f"Bearer {token}"},
    timeout=15,
)
print(f"HTTP {rp.status_code}")
if rp.status_code == 200:
    projects = rp.json().get("resources", [])
    if not projects:
        print("No projects found. You need to create one in Watsonx.ai.")
    for p in projects:
        guid = p.get("metadata", {}).get("guid", "?")
        name = p.get("entity", {}).get("name", "?")
        print(f"  ID   : {guid}")
        print(f"  Name : {name}")
        print()
else:
    print(rp.text[:600])

print()
print("--- Verifying model availability (no project needed) ---")
# Try generating with the found project or without
models = ["ibm/granite-13b-chat-v2", "ibm/granite-3-8b-instruct", "ibm/granite-3-2b-instruct"]
for m in models:
    # Try generating with current project ID first
    pid = os.getenv("IBM_PROJECT_ID","").strip()
    ep  = f"{WX_URL}/ml/v1/text/generation?version=2023-05-29"
    body = {
        "model_id":   m,
        "project_id": pid,
        "input":      "Hello",
        "parameters": {"max_new_tokens": 10},
    }
    rv = requests.post(ep, json=body,
                       headers={"Authorization": f"Bearer {token}","Content-Type":"application/json"},
                       timeout=20)
    status = rv.status_code
    if status == 200:
        gen = rv.json().get("results",[{}])[0].get("generated_text","").strip()
        print(f"  WORKS  {m}  ->  \"{gen}\"")
    else:
        snippet = rv.text[:120].replace("\n"," ")
        print(f"  {status}    {m}  ->  {snippet}")
