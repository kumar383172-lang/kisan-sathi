from dotenv import load_dotenv, dotenv_values
import os

print("=== .env keys (masked) ===")
vals = dotenv_values(".env")
for k, v in vals.items():
    masked = v[:8] + "..." + v[-4:] if v and len(v) > 14 else (v or "(empty)")
    print(f"  {k} = {masked}")

load_dotenv()
groq_key   = os.getenv("GROQ_API_KEY", "").strip()
gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
ibm_key    = os.getenv("IBM_API_KEY", "").strip()
ibm_pid    = os.getenv("IBM_PROJECT_ID", "").strip()

BAD = ("", "your_groq_api_key_here", "your_gemini_api_key_here",
       "your_ibm_cloud_api_key_here", "your_watsonx_project_id_here")

has_groq   = groq_key not in BAD
has_gemini = gemini_key not in BAD
has_ibm    = ibm_key not in BAD and ibm_pid not in BAD

print()
print("=== Provider detection ===")
print(f"  _has_groq()   = {has_groq}   key_prefix={groq_key[:16] if groq_key else '(not set)'}")
print(f"  _has_gemini() = {has_gemini}   key_prefix={gemini_key[:16] if gemini_key else '(not set)'}")
print(f"  has_ibm()     = {has_ibm}")
print()
if has_groq:
    print("  ACTIVE PROVIDER --> Groq")
elif has_gemini:
    print("  ACTIVE PROVIDER --> Gemini")
elif has_ibm:
    print("  ACTIVE PROVIDER --> IBM Watsonx")
else:
    print("  ACTIVE PROVIDER --> NONE (smart fallback only)")
    print()
    print("  FIX: the GROQ_API_KEY must be in your .env file (not .env.example)")
    print("  Copy the key from .env.example into .env")
