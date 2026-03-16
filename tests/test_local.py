"""
tests/test_local.py — Stage 1 + 2 local test (no Telegram/Supabase needed)

Stage 1: Pinecone connectivity + search for all 3 namespaces
Stage 2: Groq LLM call via each vertical's agent.get_response()

Usage:
    cd /Users/mrhustle/internship-ai-project
    python tests/test_local.py
"""

import os
import sys
from pathlib import Path

# ── Load env from first .env found (receptionist has PINECONE_API_KEY) ────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "02-receptionist" / ".env")
except ImportError:
    pass  # dotenv not installed — keys must be in shell environment

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

PASS  = "[PASS]"
FAIL  = "[FAIL]"
SKIP  = "[SKIP]"


def check(label: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"{status} {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


# ── Stage 1: Pinecone ─────────────────────────────────────────────────────────
print("\n── Stage 1: Pinecone ─────────────────────────────────────────────────")

if not PINECONE_API_KEY:
    print(f"{FAIL} PINECONE_API_KEY not set. Add it to .env or ~/.zprofile")
    sys.exit(1)

try:
    from pinecone import Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index("ai-agent-platform")
    check("Pinecone connection OK", True)
except Exception as e:
    check("Pinecone connection", False, str(e))
    sys.exit(1)

NAMESPACES = [
    ("biz_intern_receptionist", "working hours"),
    ("biz_intern_callcenter",   "refund"),
    ("biz_intern_hotel",        "check-in time"),
]

pinecone_ok = True
for namespace, query in NAMESPACES:
    try:
        results = index.search(
            namespace=namespace,
            query={"inputs": {"text": query}, "top_k": 3},
            fields=["question", "answer"]
        )
        hits = results.get("result", {}).get("hits", [])
        ok = check(
            namespace,
            len(hits) > 0,
            f"search returned {len(hits)} results for \"{query}\""
        )
        if not ok:
            pinecone_ok = False
    except Exception as e:
        check(namespace, False, str(e))
        pinecone_ok = False

# ── Stage 2: Groq via agent.get_response() ───────────────────────────────────
print("\n── Stage 2: Groq + Agent Logic ───────────────────────────────────────")

if not GROQ_API_KEY:
    print(f"{SKIP} Groq test — GROQ_API_KEY not set. Get free key at console.groq.com")
    print("\nResult: Stage 1 complete. Add GROQ_API_KEY to .env to run Stage 2.")
    sys.exit(0 if pinecone_ok else 1)

# Verify Groq connection first
try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
    groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=5
    )
    check("Groq connection OK", True)
except Exception as e:
    check("Groq connection", False, str(e))
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent

AGENT_TESTS = [
    {
        "label":   "Receptionist agent",
        "folder":  "02-receptionist",
        "message": "What are your working hours?",
        "env_key": "BIZ_NAME",
        "env_val": "City Clinic",
    },
    {
        "label":   "Call center agent",
        "folder":  "03-call-center",
        "message": "I want a refund",
        "env_key": "COMPANY_NAME",
        "env_val": "TechMart India",
    },
    {
        "label":   "Hotel agent",
        "folder":  "04-hotel-agent",
        "message": "What time is check-in?",
        "env_key": "HOTEL_NAME",
        "env_val": "Grand Mahal Hotel",
    },
]

all_ok = pinecone_ok
for test in AGENT_TESTS:
    folder = REPO_ROOT / test["folder"]
    # Set required env vars before importing agent
    os.environ["GROQ_API_KEY"]    = GROQ_API_KEY
    os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
    os.environ[test["env_key"]]   = test["env_val"]

    # Add folder to path so `from prompts import ...` works inside agent.py
    if str(folder) in sys.path:
        sys.path.remove(str(folder))
    sys.path.insert(0, str(folder))

    # Remove cached modules from previous iteration
    for mod in ["agent", "prompts"]:
        sys.modules.pop(mod, None)

    try:
        import agent
        response = agent.get_response(test["message"], [])
        text = response.get("text", "")
        intent = response.get("intent", "unknown")
        ok = check(
            test["label"],
            bool(text) and intent != "unknown",
            f'intent: {intent}, text: "{text[:60]}..."'
        )
        all_ok = all_ok and ok
    except Exception as e:
        check(test["label"], False, str(e))
        all_ok = False
    finally:
        sys.path.pop(0)

print()
if all_ok:
    print("All checks passed.")
else:
    print("Some checks failed — see [FAIL] lines above.")
    sys.exit(1)
