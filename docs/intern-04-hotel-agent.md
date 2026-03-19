# Hotel & Restaurant Agent Bot
## Semester Project Documentation

---

**Project Title:** AI-Powered Hotel & Restaurant Agent Bot on Telegram
**Intern Name:** [INTERN NAME]
**College Roll Number:** [ROLL NUMBER]
**College / Institution:** [COLLEGE NAME]
**Guide / Supervisor:** [GUIDE NAME]
**Academic Year:** 2025–26
**Submission Date:** [SUBMISSION DATE]

---

## Abstract

This project details the design and implementation of an AI-powered Hotel & Restaurant Concierge Bot deployed on Telegram. The bot operates as a dual-mode agent, handling both room bookings and food/room-service orders within a single conversational interface. Demonstrated for "Grand Mahal Hotel," the system integrates the Groq API (LLaMA-3.3-70B) for natural language understanding and action extraction, Pinecone for hotel FAQ retrieval, and Supabase for persistent room booking and food order records. The bot maintains an in-memory conversation history per user and injects the full menu and room rate catalogue into every LLM prompt, enabling accurate pricing and availability responses. Testing confirmed reliable intent switching between hotel and restaurant modes, correct total amount calculation, and accurate Supabase persistence for both booking and order actions. The project demonstrates a practical AI concierge capable of replacing front-desk functions for a boutique hotel or restaurant.

---

## 1. Introduction

### 1.1 Problem Statement

Hotels and restaurants face significant front-desk overhead from repetitive guest queries: room rates, availability, check-in/check-out policies, menu items, and room service orders. A guest-facing AI concierge available 24/7 on Telegram can handle these tasks instantly, reducing staff workload and improving guest experience — particularly for international or late-arriving guests.

### 1.2 Objectives

- Allow guests to book rooms conversationally by collecting all required details (guest name, check-in/check-out dates, room type, guest count).
- Allow guests to place food orders (dine-in or room service) by selecting items from a menu.
- Answer hotel FAQs using a vector knowledge base.
- Calculate totals automatically and persist both bookings and orders to Supabase.

### 1.3 Scope

This implementation covers:
- Dual-mode intent detection: `room_booking` and `food_order` within a single bot.
- Room rate catalogue (Standard ₹2,500/night, Deluxe ₹4,500/night, Suite ₹8,000/night) injected into every prompt.
- Restaurant menu (South Indian, North Indian, Rice & Biryani, Beverages) injected into every prompt.
- Booking persistence to `hotel_bookings` table.
- Food order persistence to `food_orders` table.
- Hotel FAQ answering via Pinecone.

Out of scope: real-time room availability checking, payment processing, and kitchen display integration (Phase 2).

---

## 2. Literature Review / Background

### 2.1 AI Concierge Systems in Hospitality

The hospitality industry has been an early adopter of conversational AI, with major chains deploying chatbots for booking assistance, upselling, and concierge services. Research by Oracle Hospitality (2022) found that 73% of guests prefer self-service technology for routine requests. Telegram-based concierge bots offer a lightweight alternative to expensive custom apps for independent hotels.

### 2.2 Multi-Intent Agents

Handling multiple distinct transaction types (booking vs. food order) within a single conversational agent requires robust intent switching. The LLaMA-3.3-70B model's instruction-following capability allows the system prompt to define both modes and trust the model to switch between them based on conversation context — without explicit intent routing code.

### 2.3 Prompt-Injected Product Catalogues

Rather than querying a database for menu prices on every request, the full menu and room rate catalogue is injected directly into the system prompt. This approach eliminates a database round-trip and ensures the LLM has complete pricing context for total calculation. The tradeoff — a larger prompt — is acceptable given Groq's high token throughput.

### 2.4 Supabase for Hospitality Data

Two dedicated tables (`hotel_bookings` and `food_orders`) store structured transaction records with proper typing (date fields for bookings, JSONB for order item arrays). The real-time subscription feature enables a hotel management dashboard to display live bookings and orders.

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
Guest (Telegram User)
       |
       | (text message)
       v
python-telegram-bot 21.x  [Polling mode]
       |
       |--- /start --> GREETING_RESPONSE (warm welcome, no LLM call)
       |
       |--- Free text --> agent.get_response()
                             |
                             | 1. get_faq_context(user_message)
                             |         |
                             |    Pinecone search_records()
                             |    Namespace: biz_intern_hotel
                             |    Top-3 semantic matches
                             |         |
                             | 2. Build SYSTEM_PROMPT
                             |    (hotel_name + ROOM_RATES + MENU
                             |     + faq_context + history)
                             |         |
                             | 3. Groq API → LLaMA-3.3-70B
                             |         |
                             | 4. Parse JSON response
                             |    {text, intent, action, action_data, escalate}
                             |         |
                             |--- action == "book_room"?
                             |         YES → supabase.hotel_bookings.insert()
                             |--- action == "place_order"?
                             |         YES → supabase.food_orders.insert()
                             |
                        log to supabase.conversations
```

### 3.2 Message Flow

1. Guest sends a message via Telegram.
2. In-memory history for the guest (last 10 messages) is retrieved.
3. `get_faq_context()` searches Pinecone for relevant hotel FAQ content.
4. The system prompt — which always includes the full room rate table and restaurant menu — is assembled and sent to Groq.
5. The LLM returns a JSON object with `text`, `intent`, `action`, and `action_data`.
6. Based on `action`:
   - `"book_room"` → insert into `hotel_bookings` (with `total_amount` pre-calculated by the LLM).
   - `"place_order"` → insert into `food_orders` (with `items` array and `total_amount`).
7. Bot reply is sent and the exchange is logged to `conversations`.

### 3.3 Component Roles

| Component | Role |
|-----------|------|
| `bot.py` | Telegram app setup, message routing, Supabase writes |
| `agent.py` | FAQ retrieval, LLM orchestration, response parsing |
| `prompts.py` | `SYSTEM_PROMPT`, `MENU`, `ROOM_RATES`, `GREETING_RESPONSE` |
| Pinecone (`biz_intern_hotel` namespace) | Hotel policy and FAQ knowledge base |
| Supabase (`hotel_bookings`) | Room booking records |
| Supabase (`food_orders`) | Food order records with JSONB items array |
| Supabase (`conversations`) | Audit log |
| Groq API | Dual-mode intent detection and response generation |

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

### 5.1 Product Catalogue Constants

Room rates and the restaurant menu are defined as module-level string constants and injected directly into every LLM prompt:

```python
MENU = """
=== RESTAURANT MENU ===
South Indian:
  • Masala Dosa         ₹120
  • Idli Sambar (4 pcs) ₹90
  • Pav Bhaji           ₹150

North Indian:
  • Butter Chicken      ₹320
  • Dal Makhani         ₹250
  • Paneer Tikka        ₹280

Rice & Biryani:
  • Veg Fried Rice      ₹180
  • Chicken Biryani     ₹350

Beverages:
  • Masala Chai         ₹40
  • Fresh Lime Soda     ₹60
"""

ROOM_RATES = """
=== ROOM TYPES & RATES ===
  • Standard Room   ₹2,500/night (AC, TV, WiFi)
  • Deluxe Room     ₹4,500/night (AC, TV, WiFi, Mini-bar, City view)
  • Suite           ₹8,000/night (AC, TV, WiFi, Mini-bar, Jacuzzi, Premium amenities)
"""
```

This approach ensures the LLM always has the complete catalogue for accurate quoting and total calculation without an additional database query.

### 5.2 Dual-Mode System Prompt

```python
SYSTEM_PROMPT = """You are a helpful AI concierge for {hotel_name}.
Handle two request types: room bookings and food/room service orders.

{room_rates}
{menu}

Respond with valid JSON only:
{{
  "text": "1-2 sentence response",
  "intent": "room_booking | food_order | faq | greeting | escalate | unknown",
  "action": "null | book_room | place_order | escalate",
  "action_data": null,
  "escalate": false
}}

For room booking, action_data:
{{ "guest_name": "...", "room_type": "standard|deluxe|suite",
   "check_in": "YYYY-MM-DD", "check_out": "YYYY-MM-DD",
   "guests_count": 1, "total_amount": calculated }}

For food order, action_data:
{{ "customer_name": "...", "room_number": "...",
   "items": [{{"name": "...", "qty": 1, "price": 120}}],
   "total_amount": calculated_total }}

FAQ Context: {faq_context}
Conversation so far: {history}
"""
```

### 5.3 Room Booking Persistence

```python
if response.get("action") == "book_room":
    data = response.get("action_data", {})
    supabase.table("hotel_bookings").insert({
        "guest_name": data.get("guest_name", ""),
        "room_type": data.get("room_type", "standard"),
        "check_in": data.get("check_in"),
        "check_out": data.get("check_out"),
        "guests_count": data.get("guests_count", 1),
        "total_amount": data.get("total_amount"),
        "telegram_user_id": str(update.effective_user.id)
    }).execute()
```

### 5.4 Food Order Persistence

Food orders use Supabase's native JSONB support for the items array:

```python
if response.get("action") == "place_order":
    data = response.get("action_data", {})
    supabase.table("food_orders").insert({
        "customer_name": data.get("customer_name", ""),
        "room_number": data.get("room_number", "Takeaway"),
        "items": data.get("items", []),      # stored as JSONB
        "total_amount": data.get("total_amount"),
        "status": "pending",
        "telegram_user_id": str(update.effective_user.id)
    }).execute()
```

### 5.5 Greeting Response

The `/start` command returns a hardcoded greeting without an LLM call, ensuring instant response for first contact:

```python
GREETING_RESPONSE = {
    "text": "Namaste! Welcome to {hotel_name}. I'm your AI concierge. I can help you book a room, place a food order, or answer any questions about our hotel. How may I assist you today?",
    "intent": "greeting",
    "action": "null",
    "action_data": None,
    "escalate": False
}
```

---

## 6. Database Design

### 6.1 Tables Used

**`hotel_bookings`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `guest_name` | text | Guest's full name |
| `room_type` | text | `standard` / `deluxe` / `suite` |
| `check_in` | date | Check-in date |
| `check_out` | date | Check-out date |
| `guests_count` | int | Number of guests |
| `total_amount` | decimal | Pre-calculated by LLM |
| `telegram_user_id` | text | Guest's Telegram ID |
| `created_at` | timestamptz | Booking timestamp |

**`food_orders`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `customer_name` | text | Guest name or room number |
| `room_number` | text | Room number or `'Takeaway'` |
| `items` | jsonb | Array of `{name, qty, price}` objects |
| `total_amount` | decimal | Order total |
| `status` | text | `pending` / `preparing` / `delivered` |
| `telegram_user_id` | text | Guest's Telegram ID |
| `created_at` | timestamptz | Order timestamp |

**`conversations`** — Shared table, filtered by `bot_id = 'hotel'`.

### 6.2 ER Overview

```
hotel_bookings                       food_orders
  id (PK)                              id (PK)
  guest_name                           customer_name
  room_type                            room_number
  check_in                             items (JSONB)
  check_out                            total_amount
  guests_count                         status
  total_amount                         telegram_user_id
  telegram_user_id ─────────────────── telegram_user_id
  created_at                           created_at
        |
        └── both relate to ── conversations.telegram_user_id
```

### 6.3 Design Decisions

- `check_in` and `check_out` are stored as typed `date` columns (unlike the receptionist bot's free-text approach), because the LLM is prompted to output `YYYY-MM-DD` format, enabling date arithmetic for stay duration and total calculation.
- The `items` JSONB column in `food_orders` allows flexible multi-item orders without a normalised order-items table, which is appropriate for this prototype scale.
- `status = 'pending'` on insert; staff update this via the admin dashboard as orders are prepared and delivered.

---

## 7. Testing & Results

### 7.1 Test Scenarios

| Scenario | Expected Behaviour | Result |
|----------|--------------------|--------|
| Guest asks "What rooms do you have?" | Room types and rates returned from prompt | Pass |
| Guest books a Deluxe room (3 nights) | Row in `hotel_bookings`, total = ₹13,500 | Pass |
| Guest orders Butter Chicken + Biryani to Room 204 | Row in `food_orders`, total = ₹670, JSONB items | Pass |
| Guest asks "What time is checkout?" | FAQ retrieved from Pinecone | Pass |
| Guest requests taxi (out of scope) | Graceful escalation to staff | Pass |
| Guest asks for menu in food order | Full menu from prompt returned | Pass |
| Groq API timeout | Fallback apology message, no crash | Pass |
| Guest books and then orders food (same session) | Context switches correctly between modes | Pass |

### 7.2 Sample Conversations

**Room booking (multi-turn):**
```
Guest:     I'd like to book a room for next weekend.
Concierge: With pleasure! We have Standard (₹2,500/night), Deluxe (₹4,500/night),
           and Suite (₹8,000/night). Which type would you prefer?
Guest:     Deluxe, for 2 guests. 22nd to 24th March.
Concierge: Most certainly! Could I have your name to confirm the booking?
Guest:     Arun Mehta.
Concierge: Your Deluxe room is confirmed for Arun Mehta, 22–24 March (2 nights).
           Total: ₹9,000. We look forward to welcoming you!
```

**Food order:**
```
Guest:     Can I order room service? I'm in Room 301.
Concierge: Of course! What would you like to order? Our menu is available —
           would you like South Indian, North Indian, or something else?
Guest:     One Chicken Biryani and two Masala Chais please.
Concierge: Your order has been placed — Chicken Biryani (₹350) and 2×Masala
           Chai (₹80). Total: ₹430. Expected delivery: 25–30 minutes. 🙏
```

### 7.3 Observations

- The LLM reliably calculated multi-night totals and multi-item order totals when room rates and menu prices were in the prompt.
- Intent switching between room booking and food order modes within the same session worked correctly due to the sliding history window.
- The Indian hospitality phrases ("With pleasure", "Most certainly", "Namaste") created a warm conversational tone appreciated in informal testing.

---

## 8. Phase 2 Enhancement Plan

### Part A: Bot-Specific Enhancements

**1. Online Payment Integration (Razorpay)**
Integrate Razorpay's payment link API to generate a payment link upon booking confirmation. The link is sent to the guest via Telegram; on successful payment, the booking status in `hotel_bookings` is updated from `'pending'` to `'confirmed'` via a Razorpay webhook.

**2. Real-Time Room Availability System**
Introduce a `room_inventory` table tracking availability per room type per date. Before confirming a booking, the bot queries this table to prevent double-booking. The dashboard displays a live availability grid by room type and date range.

**3. Guest Loyalty Points System**
Track repeat guests by their `telegram_user_id` in a `guest_profiles` table. Each confirmed booking earns points (e.g., 1 point per ₹100 spent). Points are displayed on the guest's next interaction, and a threshold (e.g., 500 points) unlocks a complimentary upgrade.

**4. Food Order Kitchen Display System**
When a food order is placed, send a formatted notification to a kitchen staff WhatsApp group via Twilio's WhatsApp Business API: order items, quantity, room number, and timestamp. This replaces manual phone calls to the kitchen and reduces order errors.

**5. Check-Out Bill Generation with PDF Receipt**
On check-out, aggregate all room charges and food orders for the guest from Supabase. Generate a formatted PDF bill using ReportLab and send it to the guest as a Telegram document, providing a digital receipt without requiring front-desk interaction.

---

### Part B: Shared Platform Upgrades

**1. Cloud Deployment (Railway / Render)**
Currently all bots run locally, requiring a developer machine to remain on. Deploying to Railway or Render provides persistent 24/7 hosting with automatic restarts on failure. Environment variables are managed through the platform's secrets store.

**2. Admin Dashboard v2**
Extend the existing HTML dashboard with per-bot conversation metrics (message volume, top intents, escalation rate), CSV export, and date-range filtering. For the hotel vertical specifically: live booking table, food order queue, and revenue by room type. Charts use Chart.js over the Supabase real-time feed.

**3. Shared JWT Authentication Layer**
Introduce a lightweight FastAPI service that issues JWT tokens for future web frontend access. For the hotel vertical, this enables a web-based hotel management panel for staff to view and update booking/order status.

**4. Webhook Migration**
Replace long-polling with Telegram webhooks. Webhooks eliminate continuous polling, reducing latency and resource usage. Requires a public HTTPS URL — provided by the cloud deployment step above.

**5. Automated Test Suite**
Write a pytest suite using `unittest.mock` to mock Telegram `Update` objects and Supabase responses. Tests cover room booking data extraction, food order item parsing, total amount calculation, and dual-mode intent switching.

---

## 9. Conclusion

The Hotel & Restaurant Agent Bot demonstrates the feasibility of a dual-mode AI concierge handling both room bookings and food orders within a single conversational interface on Telegram. The prompt-injected catalogue approach (embedding full menu and room rates in every LLM call) proved reliable and eliminated additional database queries, at the cost of a slightly larger prompt. Supabase's JSONB support for food order items and typed date columns for bookings enabled a clean data model appropriate for the project scope.

Key learnings include the challenge of multi-intent session management, the value of a warm conversational tone in hospitality contexts, and the practicality of letting the LLM perform total calculation rather than implementing separate arithmetic logic. The Phase 2 plan — payment integration, real-time availability, loyalty points, and kitchen notifications — charts a clear path to a production-ready hospitality concierge.

---

## 10. References

1. Telegram Bot API Documentation. https://core.telegram.org/bots/api
2. python-telegram-bot Library. https://python-telegram-bot.org/ (v21.x)
3. Groq API Documentation. https://console.groq.com/docs
4. Meta AI. LLaMA 3 Technical Report (2024). https://ai.meta.com/research/publications/
5. Pinecone Documentation. https://docs.pinecone.io
6. Supabase Documentation. https://supabase.com/docs
7. Oracle Hospitality. "Hotel 2025: Hospitality Technology Study." Oracle, 2022.
8. Lewis, P. et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020.
9. Razorpay API Documentation. https://razorpay.com/docs/api/
