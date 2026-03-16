import json
import os
from groq import Groq
from pinecone import Pinecone
from prompts import SYSTEM_PROMPT

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-agent-platform")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "biz_intern_callcenter")
pinecone_index = pc.Index(PINECONE_INDEX_NAME)
COMPANY_NAME = os.getenv("COMPANY_NAME", "TechMart India")


def get_faq_context(user_message: str) -> str:
    """Search Pinecone for relevant FAQs and return as formatted string."""
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
        role = "Customer" if msg["role"] == "user" else "Support Agent"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def get_response(user_message: str, history: list) -> dict:
    """Call Groq LLM and return parsed JSON response."""
    faq_context = get_faq_context(user_message)
    system = SYSTEM_PROMPT.format(
        company_name=COMPANY_NAME,
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
            max_tokens=400,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {
            "text": "I'm sorry, I couldn't process that. Could you please rephrase your query?",
            "intent": "unknown",
            "action": "null",
            "action_data": None,
            "escalate": False
        }
    except Exception as e:
        print(f"Groq error: {e}")
        return {
            "text": "I'm facing a technical issue. Please try again in a moment.",
            "intent": "unknown",
            "action": "null",
            "action_data": None,
            "escalate": False
        }
