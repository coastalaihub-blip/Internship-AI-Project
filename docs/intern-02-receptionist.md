# Business Receptionist Bot
## Semester Project Documentation

---

**Project Title:** AI-Powered Business Receptionist Bot on Telegram
**Intern Name:** [INTERN NAME]
**College Roll Number:** [ROLL NUMBER]
**College / Institution:** [COLLEGE NAME]
**Guide / Supervisor:** [GUIDE NAME]
**Academic Year:** 2025–26
**Submission Date:** [SUBMISSION DATE]

---

## Abstract

This project details the development of an AI-powered Business Receptionist Bot deployed on the Telegram platform for a multi-specialty clinic environment (configurable for any service business). The bot handles appointment booking, FAQ answering, and human-staff escalation through a conversational interface. The system integrates the Groq API (LLaMA-3.3-70B) for natural language processing, Pinecone for semantic FAQ retrieval, and Supabase for appointment persistence and conversation logging. Patients interact with the bot as they would a front-desk receptionist — booking appointments by sharing their name, phone number, preferred date/time, and doctor preference. The bot retrieves relevant clinic information from a vector knowledge base before each response, ensuring factual accuracy. Successful testing demonstrated accurate appointment capture across multi-turn conversations, correct FAQ answers, and graceful escalation when the patient's need exceeded the bot's scope. The project establishes a replicable template for AI-first front-desk automation.

---

## 1. Introduction

### 1.1 Problem Statement

Clinic front desks handle a high volume of repetitive patient inquiries — appointment availability, fee structures, doctor specialisations, and directions. Human receptionists are limited in availability (typically 9 AM–6 PM) and capacity. An AI receptionist available 24/7 on a platform patients already use (Telegram) can significantly reduce front-desk workload while improving patient experience.

### 1.2 Objectives

- Answer common clinic FAQs instantly using a semantic knowledge base.
- Guide patients through the appointment booking flow conversationally, collecting all required information (name, phone, date/time, doctor preference).
- Persist confirmed appointments to a relational database (Supabase) for staff access.
- Escalate complex or frustrated patient queries to human staff.

### 1.3 Scope

This implementation covers:
- FAQ answering via Pinecone vector search (top-3 relevant chunks per query).
- Multi-turn appointment booking conversation with structured data extraction.
- Appointment logging to the `appointments` table in Supabase.
- Conversation logging to the shared `conversations` table.
- Escalation intent detection and acknowledgement.

Out of scope: real-time doctor schedule querying, payment collection, and reminder notifications (Phase 2).

---

## 2. Literature Review / Background

### 2.1 Healthcare Chatbots

Studies published in the Journal of Medical Internet Research (2022) indicate that healthcare chatbots can handle 60–80% of routine patient inquiries without human intervention. Key success factors include accurate intent detection, safe escalation design, and clear communication of the bot's limitations to users.

### 2.2 Telegram as a Patient Communication Platform

Telegram's end-to-end encrypted messages and large group/broadcast capabilities make it increasingly popular in healthcare settings, particularly in South Asia and Southeast Asia where WhatsApp fatigue has driven users to alternative platforms. Telegram bot tokens are free and bot interactions require no app installation beyond Telegram itself.

### 2.3 Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation (Lewis et al., 2020) combines a retrieval step (finding relevant documents) with an LLM generation step. This approach grounds the LLM's responses in verified facts, reducing hallucination. Pinecone's serverless vector index enables sub-100ms similarity searches, making RAG practical for real-time chatbot responses.

### 2.4 Structured Output from LLMs

Enforcing JSON output from LLMs (using Groq's `response_format: {"type": "json_object"}`) enables downstream code to reliably parse intent, action, and action data fields without brittle string parsing. This technique is critical for the appointment booking flow where structured data must be extracted and written to the database.

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
Patient (Telegram User)
        |
        | (text message)
        v
python-telegram-bot 21.x  [Polling mode]
        |
        |--- /start --> GREETING_RESPONSE (hardcoded, no LLM call)
        |
        |--- Free text --> agent.get_response()
                              |
                              | 1. get_faq_context(user_message)
                              |         |
                              |    Pinecone search_records()
                              |    Namespace: biz_intern_receptionist
                              |    Top-3 semantic matches
                              |         |
                              | 2. Build SYSTEM_PROMPT
                              |    (biz_name + faq_context + history)
                              |         |
                              | 3. Groq API → LLaMA-3.3-70B
                              |         |
                              | 4. Parse JSON response
                              |    {text, intent, action, action_data, escalate}
                              |         |
                              |--- action == "book_appointment" ?
                              |         YES → supabase.appointments.insert()
                              |         NO  → reply text only
                              |
                         log to supabase.conversations
```

### 3.2 Message Flow

1. Patient sends a message to the Telegram bot.
2. The bot fetches the last 10 messages from the in-memory history for this user.
3. `get_faq_context()` embeds the message and searches Pinecone for the top-3 relevant FAQ chunks.
4. The Groq API is called with the assembled system prompt, returning a structured JSON response.
5. If the LLM sets `action = "book_appointment"`, the `action_data` dictionary is written to the `appointments` table.
6. The `text` field is sent back to the patient.
7. The full exchange is logged to `conversations`.

### 3.3 Component Roles

| Component | Role |
|-----------|------|
| `bot.py` | Telegram app setup, command handlers, message routing |
| `agent.py` | Orchestration: FAQ retrieval, LLM call, response parsing |
| `prompts.py` | `SYSTEM_PROMPT` and `GREETING_RESPONSE` templates |
| Pinecone (`biz_intern_receptionist` namespace) | Semantic FAQ knowledge base |
| Supabase (`appointments`) | Persistent appointment records |
| Supabase (`conversations`) | Audit log |
| Groq API | NLU and response generation |

---

## 4. Technology Stack

| Component | Technology | Version / Tier |
|-----------|-----------|----------------|
| Messaging platform | Telegram Bot API | — |
| Bot library | python-telegram-bot | 21.x |
| LLM inference | Groq API — LLaMA-3.3-70B-Versatile | Free tier (30 req/min) |
| Vector database | Pinecone (serverless, llama-text-embed-v2) | Free tier |
| Relational database | Supabase (PostgreSQL) | Free tier |
| Runtime | Python | 3.11+ |
| Environment management | python-dotenv | — |
| IDE | Firebase Studio / Google IDX | Cloud-hosted |

---

## 5. Implementation

### 5.1 FAQ Retrieval with Pinecone

Before every LLM call, the agent fetches semantically relevant FAQ chunks:

```python
def get_faq_context(user_message: str) -> str:
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
```

The FAQ chunks are injected into the system prompt, allowing the LLM to quote clinic-specific information (fees, timings, doctors) accurately.

### 5.2 System Prompt Design

```python
SYSTEM_PROMPT = """You are a friendly AI receptionist for {biz_name}.

Capabilities:
1. Answer FAQs (use FAQ context below)
2. Book appointments (collect: patient name, phone, date/time, doctor)
3. Escalate to staff when needed

Respond with valid JSON only:
{{
  "text": "1-2 sentence response",
  "intent": "faq | book_appointment | escalate | greeting | unknown",
  "action": "null | book_appointment | escalate",
  "action_data": null,
  "escalate": false
}}

When booking, action_data must contain:
{{
  "patient_name": "...", "phone": "...",
  "appointment_datetime": "...", "doctor": "...", "notes": "..."
}}

FAQ Context: {faq_context}
Conversation so far: {history}
"""
```

### 5.3 Appointment Booking and Persistence

When the LLM determines enough information has been collected (`action = "book_appointment"`), the bot writes the appointment to Supabase:

```python
async def handle_message(update: Update, context: ...) -> None:
    response = agent.get_response(user_message, history)

    if response.get("action") == "book_appointment":
        data = response.get("action_data", {})
        supabase.table("appointments").insert({
            "patient_name": data.get("patient_name", ""),
            "phone": data.get("phone", ""),
            "appointment_datetime": data.get("appointment_datetime", ""),
            "doctor": data.get("doctor", "Any available doctor"),
            "notes": data.get("notes", ""),
            "telegram_user_id": str(update.effective_user.id)
        }).execute()
```

### 5.4 Escalation Handling

When `escalate = true` in the JSON response, the bot sends a human-staff notification message and alerts the patient that a staff member will follow up. The `conversations` table records `intent = "escalate"` for later review.

### 5.5 Knowledge Base Population

FAQ entries are loaded into Pinecone using the `llama-text-embed-v2` embedding model. Each record includes `question` and `answer` fields in the `biz_intern_receptionist` namespace. Sample FAQ topics include consultation fees, operating hours, available specialties, and insurance acceptance.

---

## 6. Database Design

### 6.1 Tables Used

**`appointments`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `patient_name` | text | Patient's full name |
| `phone` | text | Contact phone number |
| `appointment_datetime` | text | Requested date and time (free text) |
| `doctor` | text | Preferred doctor or 'Any available' |
| `notes` | text | Additional notes from conversation |
| `telegram_user_id` | text | Patient's Telegram ID |
| `created_at` | timestamptz | Booking timestamp |

**`conversations`** — Shared table, filtered by `bot_id = 'receptionist'`.

### 6.2 ER Overview

```
appointments
  id (PK)
  patient_name
  phone
  appointment_datetime
  doctor
  notes
  telegram_user_id ── relates to ── conversations.telegram_user_id

conversations
  id (PK)
  bot_id = 'receptionist'
  telegram_user_id
  user_message
  bot_response
  intent
  created_at
```

### 6.3 Design Decisions

- `appointment_datetime` is stored as free text rather than a typed `timestamptz` to accommodate varied patient input formats ("next Monday afternoon", "15th March 10am"). A Phase 2 enhancement will normalise this field using a date parsing step.
- The `doctor` field defaults to "Any available doctor" when the patient has no preference, simplifying staff assignment.

---

## 7. Testing & Results

### 7.1 Test Scenarios

| Scenario | Expected Behaviour | Result |
|----------|--------------------|--------|
| Patient asks "What are your consultation fees?" | FAQ retrieved from Pinecone, accurate answer | Pass |
| Patient books appointment (all details provided) | Appointment row inserted in Supabase | Pass |
| Patient books appointment (missing phone) | Bot asks for phone number before finalising | Pass |
| Patient expresses anger ("This is ridiculous!") | `escalate = true`, human-staff message sent | Pass |
| Unknown question not in FAQ | Graceful "I'll check with staff" response | Pass |
| Pinecone unavailable | Fallback message, no crash | Pass |
| Patient sends /start | Namaste greeting returned instantly | Pass |

### 7.2 Sample Conversations

**Appointment booking (multi-turn):**
```
Patient:     Hi, I need to book an appointment.
Bot:         Namaste! I'd be happy to help you book an appointment. Kindly share
             your name and preferred date and time.
Patient:     My name is Deepa Sharma, I'd like to come on Saturday at 11am.
Bot:         Thank you, Deepa! Which doctor would you prefer, or shall I book
             with any available doctor? Also, kindly share your contact number.
Patient:     Any doctor is fine. My number is 98XXXXXXXX.
Bot:         Your appointment has been confirmed for Saturday at 11 AM with the
             next available doctor. You will receive a confirmation shortly. 🙏
```

**FAQ query:**
```
Patient:     Do you accept Apollo Munich insurance?
Bot:         Yes, we accept Apollo Munich, Star Health, and HDFC ERGO insurance.
             Kindly carry your insurance card on the day of your visit.
```

### 7.3 Observations

- Multi-turn appointment collection worked reliably across 3–4 conversation turns.
- Pinecone RAG reduced hallucinated clinic details compared to using the LLM alone.
- The Indian English tone (kindly, do the needful) was well-received in informal testing.

---

## 8. Phase 2 Enhancement Plan

### Part A: Bot-Specific Enhancements

**1. Appointment Reminder System**
Send automated Telegram notifications to patients 24 hours and 1 hour before their appointment. A scheduled background job (APScheduler) will query `appointments` for upcoming bookings and send reminder messages via the Telegram Bot API.

**2. Doctor Availability Calendar with Real-Time Slot Blocking**
Integrate a doctor availability table in Supabase (`doctor_availability` with date, time, and `is_booked` flag). When a patient requests a slot, the bot checks availability before confirming, preventing double-bookings and reducing scheduling conflicts.

**3. Insurance Pre-Verification Workflow**
When a patient mentions insurance, collect their policy number and insurer name. The bot will query a mock insurance API (or an internal lookup table) and confirm whether the insurer is accepted, reducing front-desk overhead on arrival day.

**4. Multi-Language Support (Tamil / Hindi / English Auto-Detect)**
Use a lightweight language detection library (langdetect) to identify the patient's preferred language and switch the system prompt to the corresponding language template. English, Hindi, and Tamil starters will be supported in Phase 2.

**5. PDF Appointment Confirmation Generation**
After a successful booking, generate a PDF appointment slip using ReportLab containing the patient name, appointment details, clinic address, and a reference number. The PDF is sent to the patient as a Telegram document.

---

### Part B: Shared Platform Upgrades

**1. Cloud Deployment (Railway / Render)**
Currently all bots run locally, requiring a developer machine to remain on. Deploying to Railway or Render provides persistent 24/7 hosting with automatic restarts on failure. Environment variables are managed through the platform's secrets store.

**2. Admin Dashboard v2**
Extend the existing HTML dashboard with per-bot conversation metrics (message volume, top intents, escalation rate), CSV export, and date-range filtering. Charts would use Chart.js over the existing Supabase real-time feed.

**3. Shared JWT Authentication Layer**
Introduce a lightweight FastAPI service that issues JWT tokens for future web frontend access. This enables a web-based configuration panel for managing bot settings and viewing appointment reports without Supabase direct access.

**4. Webhook Migration**
Replace long-polling with Telegram webhooks. Webhooks eliminate continuous polling, reducing latency and resource usage. Requires a public HTTPS URL — provided by the cloud deployment step above.

**5. Automated Test Suite**
Write a pytest suite using `unittest.mock` to mock Telegram `Update` objects and Supabase responses. Tests cover intent classification accuracy, multi-turn conversation flows, and appointment data extraction, enabling CI/CD integration.

---

## 9. Conclusion

The Business Receptionist Bot successfully automates the core front-desk functions of a clinic: answering FAQs, booking appointments, and escalating complex queries. The RAG architecture (Pinecone + Groq) ensures that responses are grounded in verified clinic information, while the structured JSON output enables reliable downstream data processing. The Supabase `appointments` table provides clinic staff with an accessible record of all bookings.

The project demonstrated that a fully functional, domain-specific conversational agent can be built on free-tier infrastructure within a semester. The Phase 2 roadmap addresses the remaining gaps — real-time availability, reminders, multi-language support, and cloud hosting — to move the system towards production readiness.

---

## 10. References

1. Telegram Bot API Documentation. https://core.telegram.org/bots/api
2. python-telegram-bot Library. https://python-telegram-bot.org/ (v21.x)
3. Groq API Documentation. https://console.groq.com/docs
4. Meta AI. LLaMA 3 Technical Report (2024). https://ai.meta.com/research/publications/
5. Pinecone Documentation. https://docs.pinecone.io
6. Supabase Documentation. https://supabase.com/docs
7. Lewis, P. et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020.
8. Palanica, A. et al. "Healthcare Chatbots." Journal of Medical Internet Research, 2022.
