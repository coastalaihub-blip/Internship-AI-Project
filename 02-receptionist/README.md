# 02 — Business Receptionist Bot

An AI receptionist for a clinic or medical office. Handles appointment booking, answers FAQs using Pinecone, and escalates to human staff when needed.

---

## What It Does

- Greets patients and offers help
- Answers clinic FAQs (working hours, doctors, fees, location, etc.) via Pinecone RAG
- Books appointments by collecting name, phone, date/time, doctor preference
- Logs every conversation to Supabase
- Escalates complex issues to human staff

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in all 5 values

# 3. Upload FAQs to Pinecone (one-time)
python knowledge/upload_faqs.py

# 4. Run the bot
python bot.py
```

---

## Example Conversations

**FAQ Query:**
```
User: What are your working hours?
Bot:  We are open Monday to Saturday, 9 AM to 7 PM. We are closed on Sundays and public holidays.
```

**Booking Flow:**
```
User: I want to book an appointment
Bot:  I'd be happy to help you book an appointment! Could you please share your name and preferred date and time?

User: I'm Anita Sharma, want to come Friday at 3pm
Bot:  Thank you, Anita! I've noted Friday at 3 PM for you. Which doctor would you prefer, or shall I book with any available doctor?

User: Dr. Priya Nair please
Bot:  Your appointment with Dr. Priya Nair has been booked for Friday at 3 PM. You'll receive a confirmation. Please arrive 10 minutes early. See you soon!
```

**Escalation:**
```
User: I'm having chest pain and need urgent help
Bot:  Please call 108 immediately for emergency ambulance. Our first-aid number is 080-12345678. I'm connecting you with our staff right now. 📞
```

**Insurance Query:**
```
User: Do you accept Star Health insurance?
Bot:  Yes, we accept Star Health along with HDFC Ergo and Mediclaim. Please carry your insurance card and ID proof when visiting.
```

**Rescheduling:**
```
User: I need to reschedule my appointment tomorrow
Bot:  Of course! Please share your name and your preferred new date and time, and I'll get that updated for you.
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | List capabilities |

---

## File Structure

```
02-receptionist/
├── bot.py          ← Telegram handlers + Supabase logging
├── agent.py        ← Groq LLM + Pinecone FAQ retrieval
├── prompts.py      ← System prompt template
├── knowledge/
│   ├── faqs.json         ← 25 clinic FAQs
│   └── upload_faqs.py    ← One-time Pinecone upload script
├── .env.example
└── requirements.txt
```

---

## Supabase Tables Used

- `conversations` — every message logged with `bot_id = 'receptionist'`
- `appointments` — created when user books an appointment

---

## Extending the Bot

**Add more FAQs:**
1. Edit `knowledge/faqs.json` — add new entries with unique IDs
2. Re-run `python knowledge/upload_faqs.py`

**Change clinic name:**
Set `BIZ_NAME=Your Clinic Name` in `.env`

**Add more doctors:**
Update the `faq_003` entry in `faqs.json` and re-upload
