# 04 — Hotel & Restaurant Agent Bot

A dual-mode AI concierge for a hotel. Handles room bookings AND restaurant food orders in a single bot — automatically detects which mode the guest needs.

---

## What It Does

**Room Booking Mode** (triggered by: "book a room", "check availability", "reservation"):
- Collects: guest name, dates, room type, number of guests
- Calculates total amount
- Writes to `hotel_bookings` Supabase table

**Food Order Mode** (triggered by: "order food", "menu", "room service"):
- Shows menu with prices
- Collects: items + quantities + room number (or "takeaway")
- Calculates total
- Writes to `food_orders` Supabase table

**Hotel FAQ Mode** (all other queries):
- Searches Pinecone for relevant hotel policies/info
- Answers check-in/check-out times, cancellation policy, amenities, etc.

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in .env values
python knowledge/upload_faqs.py   # one-time
python bot.py
```

---

## Example Conversations

**Room Booking:**
```
User: I want to book a deluxe room for 2 nights
Bot:  With pleasure! Could you please share your name and preferred check-in date?

User: Raj Kumar, checking in March 20
Bot:  Thank you, Raj! That would be March 20-22. For a Deluxe Room (₹4,500/night), the total comes to ₹9,000. Shall I confirm this booking?

User: Yes please
Bot:  Your booking is confirmed! Raj Kumar — Deluxe Room, March 20-22. Total: ₹9,000. We look forward to welcoming you!
```

**Food Order:**
```
User: I want to order some food to my room
Bot:  Most certainly! Here's our menu. What would you like to order?

User: 2 Butter Chicken and 1 Dal Makhani to room 304
Bot:  Wonderful choice! That's 2x Butter Chicken (₹640) + Dal Makhani (₹250) = ₹890 total. Room 304. Shall I confirm this order?

User: Yes
Bot:  Your order is placed! Estimated delivery: 25-30 minutes. Enjoy your meal!
```

**Hotel FAQ:**
```
User: What time is check-out?
Bot:  Check-out time is 12 noon. Late check-out until 6 PM is available for ₹500 extra, subject to availability.

User: Do you have a gym?
Bot:  Yes! Our fully-equipped gym is open from 5 AM to 10 PM, and the outdoor pool from 6 AM to 9 PM. Both are complimentary for in-house guests.
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/menu` | View restaurant menu with prices |
| `/rooms` | View room types and rates |
| `/help` | Usage guide |

---

## Menu (embedded in bot)

| Item | Price |
|------|-------|
| Masala Dosa | ₹120 |
| Idli Sambar (4 pcs) | ₹90 |
| Pav Bhaji | ₹150 |
| Butter Chicken | ₹320 |
| Dal Makhani | ₹250 |
| Paneer Tikka | ₹280 |
| Veg Fried Rice | ₹180 |
| Chicken Biryani | ₹350 |
| Masala Chai | ₹40 |
| Fresh Lime Soda | ₹60 |

---

## Room Rates

| Type | Rate/Night | Amenities |
|------|------------|-----------|
| Standard | ₹2,500 | AC, TV, WiFi |
| Deluxe | ₹4,500 | AC, TV, WiFi, Mini-bar, City view |
| Suite | ₹8,000 | AC, TV, WiFi, Mini-bar, Jacuzzi, Premium |

---

## File Structure

```
04-hotel-agent/
├── bot.py          ← Telegram handlers + Supabase logging
├── agent.py        ← Groq LLM + Pinecone FAQ retrieval
├── prompts.py      ← System prompt + menu + room rates
├── knowledge/
│   ├── faqs.json         ← 25 hotel FAQs (rooms + restaurant + general)
│   └── upload_faqs.py
├── .env.example
└── requirements.txt
```
