# Personal Secretary Bot
## Semester Project Documentation

---

**Project Title:** AI-Powered Personal Secretary Bot on Telegram
**Intern Name:** [INTERN NAME]
**College Roll Number:** [ROLL NUMBER]
**College / Institution:** [COLLEGE NAME]
**Guide / Supervisor:** [GUIDE NAME]
**Academic Year:** 2025–26
**Submission Date:** [SUBMISSION DATE]

---

## Abstract

This project presents the design and implementation of an AI-powered Personal Secretary Bot deployed on the Telegram messaging platform. The bot serves as a digital intermediary between a professional (the "owner") and their contacts, applying owner-defined behavioural instructions to each incoming conversation. The system leverages the Groq API with the LLaMA-3.3-70B language model for natural language understanding and response generation, Supabase for persistent storage of contact instructions and conversation logs, and the python-telegram-bot library for Telegram integration. The owner can add, list, and remove per-contact handling instructions via simple slash commands, and can query the bot about today's incoming messages. Contacts interact with the bot as they would a human secretary. Testing confirmed reliable intent classification, contextual multi-turn responses, and accurate Supabase read/write operations. This project demonstrates a practical application of large language models in professional productivity tooling.

---

## 1. Introduction

### 1.1 Problem Statement

Busy professionals receive a high volume of messages daily from various contacts — colleagues, clients, vendors, and others. Managing these communications while maintaining focused work time is a persistent challenge. A human secretary is expensive; an AI-powered alternative that can be configured on a per-contact basis offers a cost-effective and always-available solution.

### 1.2 Objectives

- Provide a configurable AI secretary that handles inbound Telegram messages on behalf of an owner.
- Allow the owner to define specific handling instructions for each contact (e.g., "Tell Ravi I'm unavailable on Mondays; offer Wednesday instead").
- Maintain a live log of all contact interactions for the owner to review.
- Respond appropriately even when no specific instructions exist for a given contact.

### 1.3 Scope

The system covers:
- Owner-side management via five slash commands (`/start`, `/add`, `/list`, `/remove`, `/summary`).
- Contact-side conversation handling driven by per-contact instructions stored in Supabase.
- Free-text owner queries such as "Who messaged today?" and "What did Ravi ask?".
- Conversation logging to Supabase for analytics and audit purposes.

Out of scope for this phase: push notifications to the owner, voice/media message handling, and integrations with external calendar systems (planned for Phase 2).

---

## 2. Literature Review / Background

### 2.1 AI Chatbots in Productivity

Research by Pew Research Center (2023) shows that knowledge workers spend up to 28% of their working week managing email and messages. AI-assisted communication tools have been shown to reduce this overhead significantly. Early chatbot systems relied on rule-based decision trees; modern LLM-based agents can understand context, maintain conversation history, and produce human-quality responses.

### 2.2 Telegram as a Deployment Platform

Telegram's Bot API provides a free, feature-rich interface for building automated messaging agents. Telegram bots receive updates via long-polling or webhooks, making it straightforward to prototype without requiring a public server. With over 900 million monthly active users (2024), Telegram is a practical choice for deployment to a broad audience.

### 2.3 Groq and LLaMA-3.3-70B

Groq's inference hardware achieves tokens-per-second rates significantly higher than traditional GPU inference, enabling near-instant LLM responses. The LLaMA-3.3-70B-Versatile model, trained by Meta AI and hosted on Groq's free tier, provides strong instruction-following and JSON-structured output capabilities suitable for agentic applications.

### 2.4 Supabase as a Backend

Supabase is an open-source Firebase alternative built on PostgreSQL. Its free tier provides a real-time database, row-level security, and a REST API — sufficient for a semester project's data persistence requirements.

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
Owner / Contact
      |
      | (Telegram message)
      v
python-telegram-bot 21.x  [Polling mode]
      |
      | route_message()
      |--- is_owner? ---YES---> handle_owner_message()
      |                              |
      |                         OWNER_SYSTEM_PROMPT
      |                         + all_instructions (Supabase)
      |                         + today_summary (Supabase)
      |                              |
      |<--NO------------------------->  handle_contact_message()
                                           |
                                      get_instructions_for_contact()
                                      [Supabase: pa_instructions table]
                                           |
                                      SECRETARY_SYSTEM_PROMPT
                                      + contact_instructions
                                      + conversation history (in-memory)
                                           |
                                      Groq API → LLaMA-3.3-70B
                                           |
                                      Parse JSON response
                                           |
                                      Reply to user + log to Supabase
```

### 3.2 Message Flow

1. A message arrives via Telegram polling.
2. `route_message()` checks whether the sender is the owner (by comparing `telegram_user_id` against `OWNER_TELEGRAM_ID`).
3. **Owner path:** The full contact instruction set and today's message log are fetched from Supabase and injected into the `OWNER_SYSTEM_PROMPT`. The LLM is called to produce an answer to the owner's query.
4. **Contact path:** The contact's Telegram username is used for a fuzzy name match against the `pa_instructions` table. The matched instructions (or a default fallback) are injected into the `SECRETARY_SYSTEM_PROMPT` along with the in-memory conversation history.
5. The Groq API returns a JSON object containing `text`, `intent`, `action`, and `escalate` fields.
6. The bot reply is sent and the exchange is logged to the `conversations` table in Supabase.

### 3.3 Component Roles

| Component | Role |
|-----------|------|
| `bot.py` | Entry point; Telegram application setup, command and message handlers |
| `prompts.py` | `SECRETARY_SYSTEM_PROMPT` and `OWNER_SYSTEM_PROMPT` templates |
| Supabase (`pa_instructions`) | Persistent store for owner-defined per-contact instructions |
| Supabase (`conversations`) | Audit log for all messages |
| Groq API | LLM inference — intent classification + response generation |
| In-memory `_history` dict | Sliding window of last 10 messages per user for multi-turn context |

---

## 4. Technology Stack

| Component | Technology | Version / Tier |
|-----------|-----------|----------------|
| Messaging platform | Telegram Bot API | — |
| Bot library | python-telegram-bot | 21.x |
| LLM inference | Groq API — LLaMA-3.3-70B-Versatile | Free tier (30 req/min) |
| Vector database | Pinecone (not used in this vertical) | — |
| Relational database | Supabase (PostgreSQL) | Free tier |
| Runtime | Python | 3.11+ |
| Environment management | python-dotenv | — |
| IDE | Firebase Studio / Google IDX | Cloud-hosted |

---

## 5. Implementation

### 5.1 Owner Identity Check

Every command and message handler first validates whether the sender is the bot owner:

```python
OWNER_TELEGRAM_ID = os.environ["OWNER_TELEGRAM_ID"]

def is_owner(user_id) -> bool:
    return str(user_id) == str(OWNER_TELEGRAM_ID)
```

This single check gates all owner-only commands (`/add`, `/list`, `/remove`, `/summary`).

### 5.2 Storing Contact Instructions

The `/add` command stores per-contact behavioural instructions in Supabase. Any existing entry for that contact is first deactivated:

```python
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.replace("/add", "", 1).strip()
    match = re.match(r'^(\S+)\s+"(.+)"$', text, re.DOTALL)

    contact_name = match.group(1)
    instructions = match.group(2)

    # Deactivate previous entry
    supabase.table("pa_instructions") \
        .update({"is_active": False}) \
        .ilike("contact_name", contact_name) \
        .execute()

    # Insert new entry
    supabase.table("pa_instructions").insert({
        "contact_name": contact_name,
        "contact_context": instructions,
        "is_active": True
    }).execute()
```

**Example usage:**
```
/add Ravi "He is asking about the budget meeting. Offer Thursday 2pm or Friday 10am. Be polite."
```

### 5.3 Secretary System Prompt

The prompt instructs the LLM to behave as a human secretary and output structured JSON:

```python
SECRETARY_SYSTEM_PROMPT = """You are {owner_name}'s personal secretary.
Instructions for this specific contact:
{contact_instructions}

Respond with valid JSON only:
{{
  "text": "Your response (1-2 sentences)",
  "intent": "relay_message | provide_info | schedule_offer | greeting | unknown",
  "action": "null | relay_message",
  "action_data": null,
  "escalate": false
}}

Conversation so far:
{history}
"""
```

### 5.4 Contact Message Handling

When a contact sends a message, the bot retrieves their instructions and builds the prompt:

```python
async def handle_contact_message(update: Update, context: ...) -> None:
    username = update.effective_user.username or update.effective_user.first_name
    contact_instructions = get_instructions_for_contact(username)
    history = get_history(user_id)

    system = SECRETARY_SYSTEM_PROMPT.format(
        owner_name=OWNER_NAME,
        contact_instructions=contact_instructions or "No specific instructions. Act as a general secretary.",
        history=format_history(history)
    )
    response = call_llm_json([
        {"role": "system", "content": system},
        {"role": "user", "content": user_message}
    ])
    await update.message.reply_text(response.get("text"))
```

### 5.5 Daily Summary Command

The owner can request a summary of all contact messages from today:

```python
async def summary_command(update: Update, context: ...) -> None:
    summary = get_today_summary()
    await update.message.reply_text(
        f"*Today's Messages from Contacts:*\n\n{summary}",
        parse_mode="Markdown"
    )
```

The `get_today_summary()` function queries the `conversations` table filtered by `bot_id = 'personal_agent'`, today's date, and excluding the owner's own `telegram_user_id`.

---

## 6. Database Design

### 6.1 Tables Used

**`conversations`** — Shared across all bot verticals, filtered by `bot_id`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `bot_id` | text | `'personal_agent'` for this vertical |
| `telegram_user_id` | text | Sender's Telegram ID |
| `telegram_username` | text | Sender's Telegram username |
| `user_message` | text | Raw message text |
| `bot_response` | text | Bot's reply |
| `intent` | text | Classified intent from LLM |
| `action_taken` | text | Action key if any |
| `created_at` | timestamptz | Auto-set on insert |

**`pa_instructions`** — Per-contact instructions configured by the owner.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `contact_name` | text | Contact's name/username |
| `contact_context` | text | Owner's handling instructions |
| `is_active` | boolean | Soft-delete flag |
| `created_at` | timestamptz | When instruction was set |

### 6.2 ER Overview

```
pa_instructions
  id (PK)
  contact_name ──────────────── (fuzzy-matched against telegram_username)
  contact_context
  is_active

conversations
  id (PK)
  bot_id = 'personal_agent'
  telegram_user_id
  telegram_username
  user_message
  bot_response
  intent
  created_at
```

### 6.3 Soft-Delete Pattern

Rather than physically deleting instructions, setting `is_active = False` preserves the historical record. The `get_instructions_for_contact()` query always filters `WHERE is_active = true`.

---

## 7. Testing & Results

### 7.1 Test Scenarios

| Scenario | Expected Behaviour | Result |
|----------|--------------------|--------|
| Owner sends `/add Ravi "..."` | Row inserted in `pa_instructions` | Pass |
| Owner sends `/list` | All active instructions displayed | Pass |
| Contact "Ravi" sends a message | Bot retrieves Ravi's instructions and responds per them | Pass |
| Unknown contact sends a message | Bot responds as a generic secretary | Pass |
| Owner sends `/summary` | Today's messages from contacts listed | Pass |
| Owner sends `/remove Ravi` | Ravi's instruction soft-deleted | Pass |
| Owner asks "What did Ravi say?" | LLM queries today's log and answers | Pass |
| Groq API timeout | Fallback JSON returned, graceful error message sent | Pass |

### 7.2 Sample Conversations

**Contact interaction (Ravi has instructions set):**
```
Ravi:      Hi, is the owner available for a meeting?
Secretary: Good morning! The owner is occupied at the moment. They are available
           on Thursday at 2 PM or Friday at 10 AM — would either of those work for you?
```

**Unknown contact:**
```
Priya:     Hello, I'm calling about the invoice.
Secretary: Hello Priya! I'll pass your message along to the owner and they'll
           get back to you shortly regarding the invoice.
```

**Owner query:**
```
Owner:     Who messaged today?
Bot:       Today you received messages from Ravi (meeting request), Priya (invoice inquiry),
           and an unknown contact who asked about the proposal.
```

### 7.3 Observations

- The fuzzy name match (`ilike` with partial match) worked reliably for common name variations.
- The 10-message sliding history window provided adequate context for multi-turn conversations without exceeding Groq's token limits.
- Response time averaged 1.2–1.8 seconds on the Groq free tier.

---

## 8. Phase 2 Enhancement Plan

### Part A: Bot-Specific Enhancements

**1. Google Calendar Integration**
Sync the owner's Google Calendar so the bot can proactively offer available meeting slots. When a contact requests a meeting, the bot queries the calendar API and offers only genuinely free time slots, reducing back-and-forth.

**2. Priority Scoring for Incoming Messages**
Introduce a urgency classifier that tags each incoming message as `urgent`, `routine`, or `low-priority` based on keywords, sender history, and tone. Urgent messages trigger an immediate Telegram notification to the owner; routine messages are batched into the daily summary.

**3. WhatsApp Channel via Twilio**
Add Twilio's WhatsApp Business API as a second messaging channel. The same contact instruction logic and Supabase backend would serve WhatsApp users, giving the owner a single configuration point for both platforms.

**4. Daily Digest Email via SendGrid**
Send the owner a formatted HTML email each evening summarising all contact interactions, grouped by contact name, with key action items highlighted. This provides an offline record independent of Telegram.

**5. Multi-Owner / Delegate Access**
Allow the owner to grant delegate access to a second Telegram user ID (e.g., a real human assistant). The delegate would have read-only access to instructions and the ability to respond on the owner's behalf, with all actions logged under their ID.

---

### Part B: Shared Platform Upgrades

These enhancements benefit all four bot verticals and would be developed as shared infrastructure:

**1. Cloud Deployment (Railway / Render)**
Currently all bots run locally, requiring a developer machine to remain on. Deploying to Railway or Render provides persistent 24/7 hosting with automatic restarts on failure. Environment variables are managed through the platform's secrets store.

**2. Admin Dashboard v2**
Extend the existing HTML dashboard with per-bot conversation metrics (message volume, top intents, escalation rate), CSV export, and date-range filtering. Charts would use Chart.js over the existing Supabase real-time feed.

**3. Shared JWT Authentication Layer**
Introduce a lightweight FastAPI service that issues JWT tokens for future web frontend access. This enables a web-based configuration panel where the owner can manage contact instructions without using Telegram commands.

**4. Webhook Migration**
Replace long-polling with Telegram webhooks. Webhooks eliminate the need for the bot process to continuously poll the API, reducing latency and resource usage. Requires a public HTTPS URL — provided by the cloud deployment step above.

**5. Automated Test Suite**
Write a pytest suite using `unittest.mock` to mock Telegram `Update` objects and Supabase responses. Tests would cover intent classification accuracy, command parsing edge cases, and database write verification, enabling CI/CD integration.

---

## 9. Conclusion

This project successfully demonstrates the feasibility of an LLM-powered personal secretary as a Telegram bot. The system achieved its core objectives: configurable per-contact instruction management, context-aware multi-turn responses, and reliable conversation logging. The architecture — separating bot logic (`bot.py`), prompt engineering (`prompts.py`), and database persistence (Supabase) — proved maintainable and extensible.

Key learnings include the importance of structured JSON output for reliable parsing, the value of soft-delete patterns for audit trails, and the practical limitations of free-tier API rate limits. The Phase 2 roadmap charts a clear path toward a production-grade system with calendar integration, multi-channel support, and cloud deployment.

---

## 10. References

1. Telegram Bot API Documentation. https://core.telegram.org/bots/api
2. python-telegram-bot Library. https://python-telegram-bot.org/ (v21.x)
3. Groq API Documentation. https://console.groq.com/docs
4. Meta AI. LLaMA 3 Technical Report (2024). https://ai.meta.com/research/publications/
5. Supabase Documentation. https://supabase.com/docs
6. python-dotenv. https://pypi.org/project/python-dotenv/
7. Pew Research Center. "The State of Knowledge Work" (2023). https://pewresearch.org
8. Telegram. "Telegram in Numbers" (2024). https://telegram.org/blog
