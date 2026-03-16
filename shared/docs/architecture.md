# System Architecture

## Overview

Each vertical is a single Python process — one `bot.py` file handles everything. No microservices, no servers, no webhooks.

```
Telegram User
     │
     │  (text message via Telegram API)
     ▼
┌─────────────────────────────────────┐
│          python-telegram-bot        │
│      Application.run_polling()      │
│   (polls Telegram every 0.5s)       │
└──────────────┬──────────────────────┘
               │
               │  user_id + message text
               ▼
┌─────────────────────────────────────┐
│        In-Memory History            │
│   _history[user_id] = last 10 msgs  │
│   (resets on bot restart)           │
└──────────────┬──────────────────────┘
               │
               │  history + current message
               ▼
┌─────────────────────────────────────┐
│  Pinecone search_records()          │  ← Only for verticals 02, 03, 04
│  namespace: biz_intern_{vertical}   │
│  returns: top-3 FAQ chunks          │
└──────────────┬──────────────────────┘
               │
               │  faq_context string
               ▼
┌─────────────────────────────────────┐
│         Groq API                    │
│   model: llama-3.1-70b-versatile    │
│   temperature: 0.3                  │
│   response_format: json_object      │
│                                     │
│  Returns JSON:                      │
│  { text, intent, action,            │
│    action_data, escalate }          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Action Handler              │
│  "book_appointment" → INSERT        │
│  "book_room"        → INSERT        │
│  "place_order"      → INSERT        │
│  "escalate"         → notify text   │
│  "faq"              → just reply    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Supabase                    │
│  INSERT conversations (every msg)   │
│  INSERT appointments / bookings /   │
│         food_orders (on action)     │
└─────────────────────────────────────┘
               │
               ▼
     Bot sends text reply to user
```

---

## LLM Response Schema

Every LLM call returns this JSON structure (guaranteed by `response_format={"type": "json_object"}`):

```json
{
  "text": "Response shown to user (1-2 sentences, Indian English)",
  "intent": "faq | book_appointment | book_room | place_order | escalate | unknown",
  "action": "null | book_appointment | book_room | place_order | escalate",
  "action_data": null,
  "escalate": false
}
```

When `action` is not null, `action_data` contains the relevant fields:

```json
// book_appointment
{
  "patient_name": "Anita Sharma",
  "phone": "9876543210",
  "appointment_datetime": "Tomorrow 3pm",
  "doctor": "Dr. Priya Nair",
  "notes": "First visit"
}

// book_room
{
  "guest_name": "Raj Kumar",
  "room_type": "deluxe",
  "check_in": "2026-03-20",
  "check_out": "2026-03-22",
  "guests_count": 2
}

// place_order
{
  "customer_name": "Room 204",
  "room_number": "204",
  "items": [{"name": "Butter Chicken", "qty": 1, "price": 320}, {"name": "Masala Chai", "qty": 2, "price": 40}],
  "total_amount": 400
}
```

---

## Conversation Memory

Memory is in-process Python dict — fast, zero infrastructure:

```python
_history: dict[str, list] = {}  # user_id → last 10 messages (5 exchanges)
```

- Resets on bot restart → acceptable for college submission
- Prevents context overflow (last 10 messages max)
- `user_id` from Telegram is stable per user per bot

For persistent memory across restarts, you'd need to load/save from Supabase on startup/shutdown — not needed here.

---

## Pinecone FAQ Retrieval

All FAQ verticals use **Pinecone's built-in embedding** (`llama-text-embed-v2`) — no separate embedding API:

```python
results = index.search(
    namespace=PINECONE_NAMESPACE,
    query={"inputs": {"text": user_message}, "top_k": 3},
    fields=["question", "answer"]
)
```

Returns top-3 FAQ chunks by semantic similarity. These are injected into the LLM system prompt as context.

---

## Personal Agent — Dual User Architecture

```
OWNER_TELEGRAM_ID (in .env)
         │
         ├── sends /add /list /remove /summary commands
         │   → reads/writes pa_instructions table
         │
         └── sends free-text questions about contacts
             → LLM gets full instructions context

Any other Telegram user ID = CONTACT
         │
         └── sends regular messages
             → bot looks up pa_instructions for context
             → LLM responds as owner's secretary
```

---

## Dashboard

Zero-build static HTML. Uses Supabase JS CDN client:

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

- **Live Feed**: Supabase Realtime subscription → auto-updates as messages arrive
- **Actions Log**: SQL query on appointments + hotel_bookings + food_orders
- **Stats Bar**: `COUNT(*)` queries with `.gte('created_at', today)`
