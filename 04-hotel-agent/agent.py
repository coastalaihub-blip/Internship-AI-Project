import json
import os
from groq import Groq
from pinecone import Pinecone
from prompts import SYSTEM_PROMPT, MENU, ROOM_RATES

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-agent-platform")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "biz_intern_hotel")
pinecone_index = pc.Index(PINECONE_INDEX_NAME)
HOTEL_NAME = os.getenv("HOTEL_NAME", "Grand Mahal Hotel")


def get_faq_context(user_message: str) -> str:
    """Search Pinecone for relevant hotel FAQs."""
    try:
        results = pinecone_index.search(
            namespace=PINECONE_NAMESPACE,
            query={"inputs": {"text": user_message}, "top_k": 3},
            fields=["question", "answer"]
        )
        chunks = []
        for match in results.get("result", {}).get("hits", []):
            fields = match.get("fields", {})
            q = fields.get("question", "")
            a = fields.get("answer", "")
            if q and a:
                chunks.append(f"Q: {q}\nA: {a}")
        return "\n\n".join(chunks) if chunks else "No relevant FAQ found."
    except Exception as e:
        print(f"Pinecone error: {e}")
        return "FAQ lookup unavailable."


def format_history(history: list) -> str:
    if not history:
        return "No previous messages."
    lines = []
    for msg in history:
        role = "Guest" if msg["role"] == "user" else "Concierge"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def get_response(user_message: str, history: list) -> dict:
    """Call Groq LLM and return parsed JSON response."""
    faq_context = get_faq_context(user_message)
    system = SYSTEM_PROMPT.format(
        hotel_name=HOTEL_NAME,
        room_rates=ROOM_RATES,
        menu=MENU,
        faq_context=faq_context,
        history=format_history(history)
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message}
    ]
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {
            "text": "I beg your pardon, could you please repeat that?",
            "intent": "unknown",
            "action": "null",
            "action_data": None,
            "escalate": False
        }
    except Exception as e:
        print(f"Groq error: {e}")
        return {
            "text": "I'm facing a brief technical issue. My apologies for the inconvenience.",
            "intent": "unknown",
            "action": "null",
            "action_data": None,
            "escalate": False
        }
