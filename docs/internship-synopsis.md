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

All four bots are built on a common free-tier stack. The Telegram Bot API serves as the user-facing interface, accessed via the python-telegram-bot 21.x library running in polling mode. Natural language understanding and response generation is handled by the Groq API using the LLaMA-3.3-70B-Versatile model. Three of the four verticals use Pinecone (serverless, llama-text-embed-v2 embeddings) for semantic FAQ retrieval. All bots persist data to Supabase (PostgreSQL) for conversation logging and transaction records. The runtime is Python 3.11+ and development was done on Firebase Studio / Google IDX, a cloud-hosted IDE requiring no local setup.

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

- **Per-contact instruction storage:** Owner-defined instructions are stored in Supabase with a soft-delete pattern using an `is_active` flag, preserving history while allowing updates.
- **Fuzzy name matching:** Contact lookup uses a case-insensitive partial match query to handle username variations reliably.
- **Dual prompt design:** Separate system prompts are used for contacts (secretary mode) and the owner (query mode), keeping behaviour clearly separated.
- **No vector database:** Unlike the other verticals, this bot stores knowledge as structured Supabase records rather than a Pinecone vector index, which is appropriate for the instruction-based use case.

### Database

Two Supabase tables are used. The `pa_instructions` table holds owner-defined per-contact handling rules with an active/inactive flag. The `conversations` table serves as a full message log, filtered by `bot_id = 'personal_agent'` to separate it from the other verticals.

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
- Appointments persisted to a dedicated Supabase table for staff access

### Technical Highlights

- **RAG pipeline:** A Pinecone namespace populated with clinic FAQ content (fees, hours, specialties, insurance) is searched before every LLM call, grounding responses in verified clinic information and reducing hallucination.
- **Structured appointment extraction:** The LLM is prompted to output structured appointment data only when all required fields (patient name, phone, date/time, doctor) have been collected across the conversation.
- **Free-text date storage:** Appointment datetime is stored as plain text to accommodate varied patient input formats such as "next Monday afternoon", with normalisation planned for Phase 2.
- **Empathetic tone:** Indian English style ("kindly", "do the needful") is prompted explicitly to match the target user base.

### Database

The `appointments` table stores confirmed booking records including patient name, phone, requested datetime, and preferred doctor. The shared `conversations` table logs all exchanges filtered by `bot_id = 'receptionist'`.

### Outcome

Multi-turn appointment collection worked reliably across 3–4 turns. Pinecone RAG significantly reduced hallucinated clinic details compared to LLM-only responses. Escalation on patient frustration was consistent across all high-frustration test cases.

---

## Agent Vertical 3 — Call Center Agent Bot

**Intern:** [INTERN 3 NAME] | **Roll No.:** [ROLL NUMBER] | **College:** [COLLEGE NAME]

### What It Does

An AI tier-1 customer support agent for a retail/e-commerce business (demonstrated as "TechMart India"). Handles complaints, refund enquiries, order tracking requests, account issues, and product FAQs — with empathetic responses and proactive escalation to human agents.

### Key Features

- Intent classification across 7 categories: FAQ, complaint, refund, escalation, order tracking, account, and greeting
- Complaint logging with structured metadata including complaint type, description, and urgency rating (low / medium / high)
- Escalation engine that detects angry language and triggers human-agent handoff with a reference number
- Semantic FAQ retrieval via Pinecone (return/refund policy, shipping timelines, warranty, payment methods)
- Empathy-first response pattern where frustration is acknowledged before solutions are offered

### Technical Highlights

- **Empathy instruction:** The system prompt explicitly instructs the LLM to acknowledge frustration before providing solutions. This produced a measurably better customer tone compared to an earlier version without it.
- **Urgency scoring:** Every complaint is classified as low, medium, or high urgency — enabling dashboard filtering and future SLA-based prioritisation.
- **Complaint metadata storage:** Structured complaint data (type, description, urgency) is JSON-encoded and stored in the shared `conversations` table's `action_taken` column, avoiding a separate table at prototype stage.
- **Reference number generation:** A per-customer reference is derived from the last 6 digits of their Telegram user ID, giving a lightweight ticket identifier without a dedicated ticketing system.

### Database

All conversation and complaint data is stored in the shared `conversations` table filtered by `bot_id = 'call_center'`. Complaint metadata is embedded as JSON in the `action_taken` column. A dedicated `support_tickets` table with status tracking is planned for Phase 2.

### Outcome

The bot handled all tier-1 support scenarios reliably. The empathy-first instruction produced consistent acknowledgement-before-solution responses. Urgency scoring enabled meaningful complaint filtering in the admin dashboard. JSON parse fallback prevented crashes on Groq API edge cases.

---

## Agent Vertical 4 — Hotel & Restaurant Concierge Bot

**Intern:** [INTERN 4 NAME] | **Roll No.:** [ROLL NUMBER] | **College:** [COLLEGE NAME]

### What It Does

A dual-mode AI concierge for a hotel and restaurant (demonstrated as "Grand Mahal Hotel"). Within a single conversational interface, guests can book rooms, place food or room-service orders, and ask hotel FAQs. The bot switches seamlessly between both modes based on conversation context.

### Key Features

- Room booking that collects guest name, room type (Standard / Deluxe / Suite), check-in and check-out dates, and guest count, with automatic total amount calculation
- Food ordering that accepts multi-item orders from a full restaurant menu with automatic total calculation
- Dual-mode intent switching between room booking and food order within the same session
- Full menu and room rate catalogue embedded directly in the LLM prompt for accurate pricing without extra database queries
- Hotel FAQ answering via Pinecone for check-in/check-out policies, amenities, and directions

### Technical Highlights

- **Prompt-injected catalogue:** Room rates and the restaurant menu are defined as module-level string constants and injected into every LLM system prompt. This eliminates a database round-trip and allows the LLM to compute totals directly from the prompt context.
- **JSONB for food orders:** The food orders table stores order items as a PostgreSQL JSONB array of objects (name, quantity, price), allowing flexible multi-item orders without a normalised order-items table.
- **Typed date columns for bookings:** Check-in and check-out are stored as typed PostgreSQL date columns (the LLM is prompted for YYYY-MM-DD format), enabling date arithmetic for stay duration and total calculation.
- **Warm hospitality tone:** Indian hospitality phrases ("With pleasure", "Most certainly", "Namaste") are prompted explicitly to match the hotel context.

### Database

Two dedicated tables are used. The `hotel_bookings` table stores room booking records with typed date columns and a pre-calculated total amount. The `food_orders` table stores orders with a JSONB items array and an order status field (`pending` / `preparing` / `delivered`). The shared `conversations` table logs all exchanges filtered by `bot_id = 'hotel'`.

### Outcome

Multi-night booking totals and multi-item food order totals were calculated accurately by the LLM from prompt-injected pricing. Intent switching between room and food modes within the same session worked correctly. The hospitality tone was well-received in informal testing.

---

## Shared Infrastructure

### Admin Dashboard

A real-time HTML dashboard subscribes to the Supabase `conversations` table and displays live message feeds across all four bot verticals. Each bot's conversations are separated by the `bot_id` field, allowing staff to monitor all agents from a single view.

### Shared Conversations Log

All four bots write to a single `conversations` table in Supabase, distinguished by the `bot_id` column. Each record captures the bot identifier, the user's Telegram ID and username, the user's raw message, the bot's response, the classified intent, any action taken (or JSON-encoded metadata), and a creation timestamp. This unified log powers the admin dashboard and enables cross-vertical analytics.

---

## Learning Outcomes

All four interns gained practical experience across the following skill areas during the internship:

- **LLM Integration** — calling the Groq API, enforcing structured JSON output, handling rate limits and fallback scenarios
- **Prompt Engineering** — designing system prompts for tone control, structured output, intent classification, and multi-turn context management
- **Vector Databases** — populating Pinecone namespaces with domain-specific content, running semantic similarity searches, and building a RAG pipeline
- **Database Design** — Supabase table design, soft-delete patterns, JSONB columns, and typed date fields
- **Telegram Bot Development** — using the python-telegram-bot library, managing polling mode, and writing command and message handlers
- **Conversational UX** — multi-turn state management, graceful escalation design, and error handling
- **Python** — async/await programming, environment variable management, and JSON parsing

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
