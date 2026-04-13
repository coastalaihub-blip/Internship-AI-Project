# Internship Project Synopsis
## AI-Powered Telegram Bot Agents — All Verticals

---

**Organisation / Company:** [ORGANISATION NAME]
**Internship Period:** 2025–26
**Academic Year:** 2025–26
**Prepared By:** [SUPERVISOR / MENTOR NAME]
**Document Purpose:** Synopsis for submission to intern colleges/institutions

---

## Overview

This internship programme engaged four interns, each owning an independent but architecturally consistent AI agent built on the Telegram messaging platform. All four agents share the same free-tier technology stack and a common database layer, while targeting different real-world business domains. The interns gained hands-on experience in LLM integration, prompt engineering, vector database usage, relational database design, and conversational UX — producing working software deployable to end users.

---

## Shared Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Messaging platform | Telegram Bot API | User-facing interface |
| Bot framework | python-telegram-bot 21.x | Telegram polling & handlers |
| LLM inference | Groq API — LLaMA-3.3-70B-Versatile | Natural language understanding & generation |
| Vector database | Pinecone (serverless, llama-text-embed-v2) | Semantic FAQ retrieval (RAG) |
| Relational database | Supabase (PostgreSQL) | Persistent storage & audit logs |
| Runtime | Python 3.11+ | All bot implementations |
| IDE | Firebase Studio / Google IDX | Cloud-hosted development environment |

---

## Common Architecture Pattern

All four bots follow the same core pipeline:

```
User (Telegram) → python-telegram-bot (polling)
    → In-memory conversation history (last 10 messages)
    → [Optional] Pinecone vector search — top-3 FAQ chunks
    → Groq API (LLaMA-3.3-70B) — structured JSON output
    → Parse action: persist to Supabase or escalate
    → Reply to user + log to conversations table
```

Structured JSON output from the LLM (enforced via `response_format`) ensures reliable downstream parsing across all verticals.

---

## Agent Vertical 1 — Personal Secretary Bot

**Intern:** [INTERN 1 NAME] | **Roll No.:** [ROLL NUMBER] | **College:** [COLLEGE NAME]

### What It Does

An AI personal secretary that manages inbound Telegram messages on behalf of a professional (the "owner"). The owner pre-configures handling instructions for each contact via slash commands; the bot applies those instructions when contacts message in.

### Key Features

- Owner-side commands: `/add`, `/list`, `/remove` (per-contact instructions), `/summary` (today's message log)
- Contact-side: bot acts as a human secretary, applying owner-defined rules per contact
- Owner can ask free-text queries ("Who messaged today?", "What did Ravi say?")
- Multi-turn conversation history (in-memory sliding window)
- All interactions logged to Supabase for audit and review

### Technical Highlights

- **Per-contact instruction storage:** `pa_instructions` table in Supabase with soft-delete pattern (`is_active` flag)
- **Fuzzy name matching:** `ilike` query against contact names to handle username variations
- **Dual prompt design:** separate `SECRETARY_SYSTEM_PROMPT` (for contacts) and `OWNER_SYSTEM_PROMPT` (for owner queries)
- **No Pinecone:** knowledge is stored in structured Supabase instructions, not a vector index

### Database Tables

| Table | Purpose |
|-------|---------|
| `pa_instructions` | Owner-defined per-contact handling rules |
| `conversations` | Full message log (filtered by `bot_id = 'personal_agent'`) |

### Outcome

The bot reliably intercepted contact messages, applied per-contact instructions, and provided the owner with a daily conversation digest. Intent classification (relay, schedule, escalate) worked correctly across all tested scenarios.

---

## Agent Vertical 2 — Business Receptionist Bot

**Intern:** [INTERN 2 NAME] | **Roll No.:** [ROLL NUMBER] | **College:** [COLLEGE NAME]

### What It Does

A 24/7 AI front-desk receptionist for a clinic (or any service business). Patients interact conversationally to book appointments, ask FAQs about fees and hours, and escalate when needed. Demonstrated for a multi-specialty clinic; configurable for any domain.

### Key Features

- Appointment booking via multi-turn conversation (collects name, phone, date/time, doctor preference)
- Semantic FAQ answering using Pinecone RAG (top-3 clinic-specific chunks per query)
- Escalation detection for complex or frustrated patient queries
- Instant `/start` greeting without an LLM call
- Appointments persisted to dedicated Supabase table for staff access

### Technical Highlights

- **RAG pipeline:** Pinecone namespace `biz_intern_receptionist` with clinic FAQ (fees, hours, specialties, insurance)
- **Structured appointment extraction:** LLM outputs `action_data` with `patient_name`, `phone`, `appointment_datetime`, `doctor` when all details are collected
- **Free-text date storage:** `appointment_datetime` stored as text to accommodate varied patient input formats ("next Monday afternoon")
- **Empathetic tone:** Indian English style (kindly, do the needful) prompted explicitly

### Database Tables

| Table | Purpose |
|-------|---------|
| `appointments` | Confirmed appointment records |
| `conversations` | Conversation log (filtered by `bot_id = 'receptionist'`) |

### Outcome

Multi-turn appointment collection worked reliably across 3–4 turns. Pinecone RAG significantly reduced hallucinated clinic details compared to LLM-only responses. Escalation on patient frustration was consistent across all high-frustration test cases.

---

## Agent Vertical 3 — Call Center Agent Bot

**Intern:** [INTERN 3 NAME] | **Roll No.:** [ROLL NUMBER] | **College:** [COLLEGE NAME]

### What It Does

An AI tier-1 customer support agent for a retail/e-commerce business (demonstrated as "TechMart India"). Handles complaints, refund enquiries, order tracking requests, account issues, and product FAQs — with empathetic responses and proactive escalation to human agents.

### Key Features

- Intent classification across 7 categories: `faq`, `complaint`, `refund`, `escalate`, `track_order`, `account`, `greeting`
- Complaint logging with structured metadata: complaint type, description, and urgency rating (`low`/`medium`/`high`)
- Escalation engine: detects angry language and triggers human-agent escalation with a reference number
- Semantic FAQ retrieval via Pinecone (return/refund policy, shipping, warranty, payment methods)
- Empathy-first response pattern: frustration acknowledged before solutions are offered

### Technical Highlights

- **Empathy instruction:** system prompt explicitly instructs the LLM to acknowledge frustration before providing solutions — measurably improved tone in testing
- **Urgency scoring:** complaint metadata includes urgency level, enabling dashboard filtering and SLA prioritisation
- **Complaint metadata in `action_taken`:** JSON-encoded complaint data stored in the shared `conversations` table, avoiding a separate table at this prototype stage
- **Reference number generation:** last 6 digits of `telegram_user_id` used as a per-customer reference

### Database Tables

| Table | Purpose |
|-------|---------|
| `conversations` | Full log with complaint metadata in `action_taken` column (filtered by `bot_id = 'call_center'`) |

### Outcome

The bot handled all tier-1 support scenarios reliably. The empathy-first instruction produced consistent acknowledgement-before-solution responses. Urgency scoring enabled meaningful complaint filtering in the admin dashboard. JSON parse fallback prevented crashes on Groq API edge cases.

---

## Agent Vertical 4 — Hotel & Restaurant Concierge Bot

**Intern:** [INTERN 4 NAME] | **Roll No.:** [ROLL NUMBER] | **College:** [COLLEGE NAME]

### What It Does

A dual-mode AI concierge for a hotel and restaurant (demonstrated as "Grand Mahal Hotel"). Within a single conversational interface, guests can book rooms, place food/room-service orders, and ask hotel FAQs. The bot switches seamlessly between both modes based on conversation context.

### Key Features

- **Room booking:** collects guest name, room type (Standard/Deluxe/Suite), check-in/check-out dates, guest count; calculates total amount
- **Food ordering:** accepts multi-item orders from a full restaurant menu with automatic total calculation
- **Dual-mode intent switching:** context switches between `room_booking` and `food_order` within the same session
- **Prompt-injected catalogue:** full menu and room rate table embedded in every LLM prompt for accurate pricing without extra DB queries
- **Hotel FAQ:** Pinecone RAG for check-in/check-out policies, amenities, directions, etc.

### Technical Highlights

- **Prompt-injected catalogue approach:** room rates and menu defined as module-level string constants (`ROOM_RATES`, `MENU`) and injected into every system prompt — eliminates a DB round-trip, enables LLM to compute totals directly
- **JSONB for food orders:** `items` column in `food_orders` stores array of `{name, qty, price}` objects natively in PostgreSQL JSONB
- **Typed date columns for bookings:** `check_in` / `check_out` stored as PostgreSQL `date` type (LLM prompted for `YYYY-MM-DD` format), enabling date arithmetic
- **Warm hospitality tone:** Indian hospitality phrases ("With pleasure", "Most certainly", "Namaste") prompted explicitly

### Database Tables

| Table | Purpose |
|-------|---------|
| `hotel_bookings` | Room booking records with typed date columns and pre-calculated total |
| `food_orders` | Food orders with JSONB items array and order status |
| `conversations` | Conversation log (filtered by `bot_id = 'hotel'`) |

### Outcome

Multi-night booking totals and multi-item food order totals were calculated accurately by the LLM from prompt-injected pricing. Intent switching between room and food modes within the same session worked correctly. The hospitality tone was well-received in informal testing.

---

## Shared Infrastructure

### Admin Dashboard

A real-time HTML dashboard subscribes to the Supabase `conversations` table and displays live message feeds across all four bot verticals. Each bot's conversations are filtered by `bot_id`.

### Shared `conversations` Table Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `bot_id` | text | Identifies the vertical (`personal_agent`, `receptionist`, `call_center`, `hotel`) |
| `telegram_user_id` | text | Sender's Telegram user ID |
| `telegram_username` | text | Sender's Telegram username |
| `user_message` | text | Raw user message |
| `bot_response` | text | Bot's reply |
| `intent` | text | Classified intent from LLM |
| `action_taken` | text | Action taken (or JSON-encoded metadata) |
| `created_at` | timestamptz | Auto-set on insert |

---

## Learning Outcomes

All four interns gained practical experience in the following areas:

| Skill Area | What Was Practised |
|------------|--------------------|
| LLM Integration | Calling Groq API, enforcing JSON output, handling rate limits and fallbacks |
| Prompt Engineering | System prompt design, structured output, tone control, multi-turn context |
| Vector Databases | Populating Pinecone namespaces, semantic search, RAG pipeline |
| Database Design | Supabase table design, soft-delete patterns, JSONB, typed columns |
| Telegram Bot Development | python-telegram-bot library, polling mode, command & message handlers |
| Conversational UX | Multi-turn state management, graceful escalation, error handling |
| Python | async/await, environment variable management, JSON parsing |

---

## Phase 2 Roadmap (Planned)

The following enhancements are planned across all verticals for the next phase:

**Shared Infrastructure**
- Cloud deployment to Railway or Render (24/7 hosting, no local machine required)
- Telegram webhook migration (replacing long-polling)
- Admin Dashboard v2 with Chart.js metrics, CSV export, date-range filtering
- Shared JWT authentication layer (FastAPI) for web-based admin panels
- Automated pytest suite with mocked Telegram and Supabase objects

**Vertical-Specific**
- Personal Agent: Google Calendar integration, priority scoring, WhatsApp via Twilio
- Receptionist: Appointment reminders, real-time slot availability, multi-language support (Hindi/Tamil/English)
- Call Center: Ticket tracking system, SLA breach alerts, mock CRM order lookup, sentiment analysis
- Hotel Agent: Razorpay payment integration, real-time room availability, loyalty points, kitchen WhatsApp notifications

---

## Conclusion

The internship programme successfully delivered four independent, functional AI agents on a consistent free-tier architecture. Each intern took a bot from design through implementation to tested deployment, demonstrating competence in modern AI application development. The modular, shared-infrastructure approach allowed each intern to work independently while contributing to a unified platform — mirroring real-world team development practices.

The agents are production-viable at small scale and have a clear Phase 2 roadmap to address remaining gaps in availability, payments, cloud hosting, and multi-channel support.

---

*Document prepared for institutional submission. All four interns may attach this document alongside their individual project reports.*
