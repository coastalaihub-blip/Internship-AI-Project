# Call Center Agent Bot
## Semester Project Documentation

---

**Project Title:** AI-Powered Call Center Agent Bot on Telegram
**Intern Name:** Harshitha V Shetty 
**College Roll Number:** 24251416
**College / Institution:** St. Aloysius (Deemed-to-be University)
**Guide / Supervisor:** [GUIDE NAME]
**Academic Year:** 2025–26
**Submission Date:** 26-03-2026

---

## Abstract

This project presents the design and implementation of an AI-powered Customer Support Agent Bot deployed on Telegram for a retail/e-commerce business context (demonstrated with "TechMart India" as the sample company). The bot handles customer complaints, refund enquiries, order-tracking requests, account issues, and general product FAQ queries. The system integrates the Groq API (LLaMA-3.3-70B) for empathetic, intent-aware response generation, Pinecone for semantic FAQ retrieval, and Supabase for complaint logging and conversation auditing. A core design feature is the escalation engine: when a customer expresses anger or the issue cannot be resolved autonomously, the bot immediately escalates to a human agent and logs the complaint with an urgency rating. Testing confirmed reliable complaint classification, accurate FAQ retrieval, and consistent escalation behaviour across high-frustration scenarios. The project establishes a replicable template for AI-first tier-1 customer support.

---

## 1. Introduction

### 1.1 Problem Statement

Customer support centres face high call volumes, repetitive tier-1 queries, and agent burnout. A significant proportion of incoming support requests — estimated at 60–70% for typical e-commerce operations — can be resolved without human intervention if the right information is presented accurately and empathetically. An AI-powered tier-1 support agent that handles routine queries and escalates complex ones enables human agents to focus on genuinely difficult cases.

### 1.2 Objectives

- Handle common customer support queries (order tracking, refunds, product FAQs, account issues) conversationally.
- Log all complaints with a structured format (complaint type, description, urgency) for staff follow-up.
- Detect customer frustration and escalate proactively.
- Retrieve accurate company-specific information from a vector knowledge base.

### 1.3 Scope

This implementation covers:
- FAQ answering via Pinecone vector search (top-3 chunks per query).
- Intent classification across six categories: `faq`, `complaint`, `refund`, `escalate`, `track_order`, `account`.
- Complaint logging to the `conversations` table with structured `action_data`.
- Escalation on frustration detection or explicit escalation request.
- Multi-turn conversation history (sliding window of 10 messages).

Out of scope: real-time order lookup from an OMS, payment processing, ticket status tracking (Phase 2).

---

## 2. Literature Review / Background

### 2.1 AI in Customer Support

Gartner (2023) predicts that by 2027, chatbots will handle over 50% of tier-1 customer interactions. Effective customer support chatbots require strong intent classification, empathetic tone calibration, and reliable escalation design. LLMs represent a step-change improvement over traditional BERT-based classifiers because they can handle the open-ended nature of customer complaints without exhaustive training data.

### 2.2 Empathy in AI Responses

Research in human-computer interaction (HCI) shows that customers are more satisfied with chatbot interactions when the bot acknowledges frustration before offering a solution ("I understand your concern" before "Here's what you can do"). The LLaMA-3.3-70B model was prompted with empathy instructions to reproduce this pattern.

### 2.3 Telegram as a Support Channel

Telegram is increasingly adopted as a customer support channel in South Asia and the Middle East due to its zero-cost messaging, bot API accessibility, and broad user base. Unlike custom live-chat widgets, Telegram requires no front-end development — customers use an app they already have installed.

### 2.4 Vector Search for FAQ Retrieval

Pinecone's llama-text-embed-v2 model creates dense semantic embeddings of FAQ content. When a customer asks a question, the same embedding model converts it to a vector, and Pinecone returns the most semantically similar FAQ entries. This outperforms keyword search for paraphrased queries (e.g., "where is my order" and "I haven't received my package" correctly map to the same FAQ).

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
Customer (Telegram User)
         |
         | (text message)
         v
python-telegram-bot 21.x  [Polling mode]
         |
         |--- /start --> GREETING_RESPONSE (no LLM call)
         |
         |--- Free text --> agent.get_response()
                               |
                               | 1. get_faq_context(user_message)
                               |         |
                               |    Pinecone search_records()
                               |    Namespace: biz_intern_callcenter
                               |    Top-3 semantic matches
                               |         |
                               | 2. Build SYSTEM_PROMPT
                               |    (company_name + faq_context + history)
                               |         |
                               | 3. Groq API → LLaMA-3.3-70B
                               |         |
                               | 4. Parse JSON response
                               |    {text, intent, action, action_data, escalate}
                               |         |
                               |--- action == "log_complaint"?
                               |         YES → log intent + action_data to conversations
                               |--- escalate == true?
                               |         YES → send human-agent alert message
                               |
                          log to supabase.conversations
```

### 3.2 Message Flow

1. Customer sends a message via Telegram.
2. The agent fetches the customer's in-memory conversation history (last 10 messages).
3. `get_faq_context()` queries Pinecone with the customer's message and retrieves relevant support articles.
4. The assembled system prompt (company context + FAQ chunks + history) is sent to Groq's API.
5. The LLM returns a JSON object with `text`, `intent`, `action`, `action_data`, and `escalate` fields.
6. If `action = "log_complaint"`, the complaint details from `action_data` are stored alongside the conversation record.
7. If `escalate = true`, a human-agent notification message is sent to the customer.
8. The full exchange is written to the `conversations` table.

### 3.3 Component Roles

| Component | Role |
|-----------|------|
| `bot.py` | Telegram app setup, message routing, Supabase write operations |
| `agent.py` | FAQ retrieval, LLM orchestration, JSON parsing |
| `prompts.py` | `SYSTEM_PROMPT` with empathy and escalation instructions |
| Pinecone (`biz_intern_callcenter` namespace) | Company support knowledge base |
| Supabase (`conversations`) | Complaint log and conversation audit |
| Groq API | Intent classification, empathetic response generation |

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

### 5.1 System Prompt — Empathy and Escalation

The system prompt explicitly instructs the LLM to acknowledge frustration before offering solutions and to detect high-urgency situations:

```python
SYSTEM_PROMPT = """You are a professional AI customer support agent for {company_name}.

Your personality:
- Empathetic and solution-focused
- Use Indian English (e.g., "kindly", "I understand your concern")
- Acknowledge frustration BEFORE offering solutions
- Never promise what you cannot deliver

Capabilities:
1. Answer FAQs using the context provided
2. Log complaints and support tickets
3. Escalate to human when customer is angry or issue is complex
4. Provide order/account help based on customer-provided info

Respond with valid JSON only:
{{
  "text": "1-2 sentence response",
  "intent": "faq | complaint | refund | escalate | track_order | account | greeting | unknown",
  "action": "null | log_complaint | escalate",
  "action_data": {{
    "complaint_type": "refund | delivery | product | account | billing | other",
    "description": "...",
    "urgency": "low | medium | high"
  }},
  "escalate": false
}}

FAQ Context: {faq_context}
Conversation so far: {history}
"""
```

### 5.2 Complaint Intent Classification

The LLM classifies each message across seven intent categories. When a complaint is detected, structured metadata is extracted:

```python
# Example LLM output for an angry refund complaint
{
  "text": "I sincerely apologise for the inconvenience caused. I understand how frustrating this must be. I am escalating your refund request to our senior team right away.",
  "intent": "refund",
  "action": "log_complaint",
  "action_data": {
    "complaint_type": "refund",
    "description": "Customer paid ₹4,500 for laptop stand, item not delivered after 10 days",
    "urgency": "high"
  },
  "escalate": true
}
```

### 5.3 Conversation Logging with Complaint Data

```python
async def handle_message(update: Update, context: ...) -> None:
    response = agent.get_response(user_message, history)
    bot_text = response.get("text", "I'm here to help. Please tell me more.")

    await update.message.reply_text(bot_text)

    # Log with complaint details stored in action_taken field
    action_data = response.get("action_data")
    supabase.table("conversations").insert({
        "bot_id": "call_center",
        "telegram_user_id": str(user_id),
        "telegram_username": username,
        "user_message": user_message,
        "bot_response": bot_text,
        "intent": response.get("intent", "unknown"),
        "action_taken": json.dumps(action_data) if action_data else None
    }).execute()
```

### 5.4 Escalation Response

When `escalate = true`, the bot appends a standard escalation message:

```python
if response.get("escalate"):
    escalation_msg = (
        "I have flagged your case as urgent. A member of our support team "
        "will contact you within 2 business hours. Your reference number is "
        f"#{str(update.effective_user.id)[-6:]}. We sincerely apologise for "
        "the inconvenience."
    )
    await update.message.reply_text(escalation_msg)
```

### 5.5 Knowledge Base Population

The Pinecone namespace `biz_intern_callcenter` contains support articles covering: return and refund policy, shipping timelines, warranty terms, account creation/login, payment methods, and common product FAQs. Each article is stored with `question` and `answer` fields using the llama-text-embed-v2 integrated embedding.

---

## 6. Database Design

### 6.1 Tables Used

**`conversations`** — Shared table, filtered by `bot_id = 'call_center'`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `bot_id` | text | `'call_center'` |
| `telegram_user_id` | text | Customer's Telegram ID |
| `telegram_username` | text | Customer's username |
| `user_message` | text | Customer's message |
| `bot_response` | text | Bot's response |
| `intent` | text | Classified intent |
| `action_taken` | text | JSON-encoded complaint data (when applicable) |
| `created_at` | timestamptz | Timestamp |

### 6.2 ER Overview

```
conversations (bot_id = 'call_center')
  id (PK)
  telegram_user_id
  user_message
  bot_response
  intent ── one of: faq | complaint | refund | escalate | track_order | account
  action_taken ── JSON: {complaint_type, description, urgency}
  created_at
```

### 6.3 Design Decisions

- Complaint metadata is stored as JSON in the `action_taken` text column rather than a separate `complaints` table. This reduces schema complexity for the prototype while retaining all structured data. A Phase 2 migration will introduce a dedicated `support_tickets` table with status tracking.
- The `conversations` table's real-time subscription (via Supabase realtime) enables the admin dashboard to display live complaint feeds without polling.

---

## 7. Testing & Results

### 7.1 Test Scenarios

| Scenario | Expected Behaviour | Result |
|----------|--------------------|--------|
| Customer asks "What is your return policy?" | FAQ retrieved from Pinecone, accurate answer | Pass |
| Customer reports non-delivery ("Where is my order?") | `intent = track_order`, empathetic response | Pass |
| Customer requests refund | `action = log_complaint`, complaint type = refund | Pass |
| Customer uses angry language ("This is ridiculous!") | `escalate = true`, reference number given | Pass |
| Customer asks about warranty | FAQ retrieved, warranty terms quoted | Pass |
| Pinecone unavailable | Fallback "FAQ unavailable" message, no crash | Pass |
| Customer sends /start | Greeting response instant, no LLM call | Pass |
| JSON parse failure from Groq | Default fallback dict returned, no crash | Pass |

### 7.2 Sample Conversations

**Refund complaint with escalation:**
```
Customer:   I ordered a phone case 2 weeks ago and still haven't received it.
            I want a full refund NOW.
Bot:        I sincerely understand your frustration, and I apologise for the
            delay with your order. I am raising an urgent refund request on
            your behalf right now. A senior team member will contact you within
            2 business hours. Reference: #847291.
```

**FAQ query:**
```
Customer:   Do you have EMI options?
Bot:        Yes, we offer no-cost EMI on orders above ₹3,000 through HDFC,
            ICICI, and Axis Bank credit cards. Kindly select the EMI option
            at checkout.
```

**Order tracking:**
```
Customer:   Can you tell me where my order ORD-20045 is?
Bot:        I understand your concern! At the moment I don't have direct access
            to our order management system, but I've noted your order number.
            Our team will send you tracking details within 1 hour. I apologise
            for the inconvenience.
```

### 7.3 Observations

- The empathy instruction in the system prompt consistently produced acknowledgement-first responses, even on the first turn.
- Urgency scoring ("high" for angry customers, "medium" for delayed orders, "low" for general queries) enabled useful filtering in the admin dashboard.
- The `action_data` JSON in `action_taken` proved valuable for manually reviewing complaint patterns during testing.

---

## 8. Phase 2 Enhancement Plan

### Part A: Bot-Specific Enhancements

**1. Sentiment Analysis Pipeline**
Integrate a lightweight sentiment classifier (using a Groq call or a local model via HuggingFace Transformers) to score each message on an anger/frustration scale before the main LLM call. Scores above a threshold trigger immediate escalation, overriding the main intent classification.

**2. Ticket Tracking System**
Introduce a dedicated `support_tickets` table with a ticket ID, status (`open` / `in_progress` / `resolved`), assigned agent, and SLA deadline. Customers can query ticket status by sending their reference number. Status updates trigger Telegram notifications to the customer.

**3. SLA Breach Alerts to Admin**
A background scheduler (APScheduler) monitors open tickets and sends a Telegram alert to a designated admin chat ID when a ticket has been open beyond its SLA window (e.g., >2 hours for high-urgency, >24 hours for medium).

**4. Mock CRM Integration (Order Lookup by Order ID)**
Add an order lookup table in Supabase (`mock_orders` with `order_id`, `status`, `expected_delivery`, `customer_name`). When a customer provides an order ID, the bot queries this table and returns real order data instead of a generic "I'll check" response.

**5. Complaint Analytics Dashboard**
Extend the admin dashboard with a complaint analytics page: complaint category breakdown (pie chart), average resolution time by category, daily complaint volume (line chart), and escalation rate. Data is aggregated from the `conversations` table using Supabase's RPC/SQL functions.

---

### Part B: Shared Platform Upgrades

**1. Cloud Deployment (Railway / Render)**
Currently all bots run locally, requiring a developer machine to remain on. Deploying to Railway or Render provides persistent 24/7 hosting with automatic restarts on failure. Environment variables are managed through the platform's secrets store.

**2. Admin Dashboard v2**
Extend the existing HTML dashboard with per-bot conversation metrics (message volume, top intents, escalation rate), CSV export, and date-range filtering. Charts would use Chart.js over the existing Supabase real-time feed.

**3. Shared JWT Authentication Layer**
Introduce a lightweight FastAPI service that issues JWT tokens for future web frontend access. This enables a web-based support admin panel with agent login, ticket assignment, and SLA views.

**4. Webhook Migration**
Replace long-polling with Telegram webhooks. Webhooks eliminate continuous polling, reducing latency and resource usage. Requires a public HTTPS URL — provided by the cloud deployment step above.

**5. Automated Test Suite**
Write a pytest suite using `unittest.mock` to mock Telegram `Update` objects and Supabase responses. Tests cover intent classification accuracy, escalation triggering logic, complaint data extraction, and fallback behaviour.

---

## 9. Conclusion

The Call Center Agent Bot demonstrates that LLM-based agents can handle the majority of tier-1 customer support interactions — FAQ answering, complaint logging, and empathetic communication — with high reliability on free-tier infrastructure. The structured JSON output model, combined with the Pinecone RAG pipeline, produces responses that are both factually accurate and contextually appropriate.

The project reinforced the importance of prompt engineering for tone: the empathy-first instruction produced a measurably better customer experience compared to an earlier version without it. The Phase 2 roadmap introduces ticket tracking, sentiment analysis, and CRM integration — the components needed to make the system production-viable for a real retail support operation.

---

## 10. References

1. Telegram Bot API Documentation. https://core.telegram.org/bots/api
2. python-telegram-bot Library. https://python-telegram-bot.org/ (v21.x)
3. Groq API Documentation. https://console.groq.com/docs
4. Meta AI. LLaMA 3 Technical Report (2024). https://ai.meta.com/research/publications/
5. Pinecone Documentation. https://docs.pinecone.io
6. Supabase Documentation. https://supabase.com/docs
7. Lewis, P. et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020.
8. Gartner. "Predicts 2023: Conversational AI Is Maturing." Gartner Research, 2023.
9. Hancock, J. T. et al. "AI-Mediated Communication." Journal of Communication, 2020.
