"""
_test_chat.py — end-to-end test of the chat pipeline inside app context
Run: python _test_chat.py
"""
import sys, os, time
os.environ["PYTHONIOENCODING"] = "utf-8"

from dotenv import load_dotenv
load_dotenv()

# ── patch stream to avoid generator complexity in test ──────
import app as _app

print("=== Provider flags ===")
print(f"  _has_groq()   = {_app._has_groq()}")
print(f"  _has_gemini() = {_app._has_gemini()}")
print(f"  has_ibm()     = {_app.has_ibm_credentials()}")
print()

# ── Test call_groq directly ─────────────────────────────────
print("=== Direct call_groq() test ===")
msgs = _app._build_messages(
    context="No live context.",
    history_text="",
    question="Reply with exactly 3 words: GROQ IS WORKING"
)
t0     = time.time()
answer = _app.call_groq(msgs, max_tokens=20)
ms     = int((time.time() - t0) * 1000)
if answer:
    print(f"  OK  [{ms} ms]  reply: {answer!r}")
else:
    print("  FAIL  call_groq() returned None")
    sys.exit(1)

# ── Test stream_groq directly ───────────────────────────────
print()
print("=== stream_groq() streaming test ===")
msgs2 = _app._build_messages(
    context="No live context.",
    history_text="",
    question="Name two Kharif crops in one short sentence."
)
chunks = []
t0 = time.time()
for chunk in _app.stream_groq(msgs2):
    chunks.append(chunk)
    sys.stdout.write(chunk)
    sys.stdout.flush()
ms = int((time.time() - t0) * 1000)
print()
if chunks:
    print(f"\n  OK  [{ms} ms]  total chunks={len(chunks)}  total_chars={sum(len(c) for c in chunks)}")
else:
    print("  FAIL  stream_groq() yielded nothing")
    sys.exit(1)

print()
print("=== All Groq tests passed — chatbot is wired correctly ===")
