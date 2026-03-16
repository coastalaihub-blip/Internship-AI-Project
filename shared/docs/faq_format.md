# FAQ Format Guide

## JSON Structure

Each `faqs.json` file is a list of FAQ objects:

```json
[
  {
    "id": "faq_001",
    "question": "What are your working hours?",
    "answer": "We are open Monday to Saturday, 9 AM to 7 PM. We are closed on Sundays and national holidays.",
    "category": "hours",
    "tags": ["hours", "timing", "open", "close"]
  }
]
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID. Format: `faq_001`, `faq_002`, etc. |
| `question` | string | Yes | The question as a user might ask it. Natural language. |
| `answer` | string | Yes | The answer. Concise, 1-3 sentences. Indian English. |
| `category` | string | Yes | Topic grouping (e.g., `hours`, `booking`, `fees`) |
| `tags` | list[string] | No | Keywords that help matching. Keep 3-6 tags. |

---

## Upload Script

Each vertical has `knowledge/upload_faqs.py`. It:
1. Reads `knowledge/faqs.json`
2. For each FAQ, creates a record with the question as the embedding text
3. Upserts into Pinecone using `llama-text-embed-v2` (built-in embedding)
4. Uses namespace `biz_intern_{vertical}`

Run once:
```bash
cd 02-receptionist
python knowledge/upload_faqs.py
```

---

## How to Extend

To add FAQs for a business:

1. Edit `knowledge/faqs.json` — add new entries with unique IDs
2. Re-run `python knowledge/upload_faqs.py`
3. New FAQs are searchable immediately

---

## Namespaces Per Vertical

| Vertical | Namespace |
|----------|-----------|
| 02-receptionist | `biz_intern_receptionist` |
| 03-call-center | `biz_intern_callcenter` |
| 04-hotel-agent | `biz_intern_hotel` |

All use the **same Pinecone index** (`ai-agent-platform`) — namespaces keep them isolated.

---

## FAQ Quality Tips

- Write questions in natural conversational language, not formal phrasing
- Include alternate phrasings as separate FAQs (e.g., "What time do you open?" AND "Are you open on weekends?")
- Keep answers under 3 sentences — the LLM will reformulate for context
- Use Indian English and Indian context (₹ for prices, Indian locations, etc.)
