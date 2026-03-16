# 01 — Personal Secretary Bot

An AI personal secretary for a busy professional (minister, CEO, executive). The owner pre-configures instructions for each contact; the bot handles all inbound messages accordingly.

---

## Two User Types

### Owner (you — the busy professional)
- Identified by `OWNER_TELEGRAM_ID` in `.env`
- Uses slash commands to configure contact handling
- Can ask free-text questions: "Who messaged today?", "What did Ravi want?"

### Contacts (everyone else)
- Regular Telegram users who message the bot
- Bot responds based on your pre-configured instructions
- If no instructions: "I'll pass your message along" response

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in .env — especially OWNER_TELEGRAM_ID and OWNER_NAME
python bot.py
```

**Get your Telegram ID:** Message @userinfobot on Telegram — it replies with your user ID.

---

## Owner Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/add <Name> "<instructions>"` | Set handling for a contact | `/add Ravi "He's asking about budget meeting. Offer Thu 2pm or Fri 10am."` |
| `/list` | Show all active instructions | `/list` |
| `/remove <Name>` | Remove a contact's instructions | `/remove Ravi` |
| `/summary` | Today's contact message log | `/summary` |
| Free text | Ask about contacts or messages | `"What did Ravi say today?"` |

---

## Example Conversations

**Owner configures contact:**
```
Owner: /add Priya "She is asking about the joint venture proposal. Tell her I need 2 more weeks to review. Offer a call on April 1st at 11 AM."
Bot:   Done. Instructions saved for Priya.
```

**Contact messages the bot:**
```
Priya: Hi, wanted to follow up on the JV proposal
Bot:   Hello Priya! I've passed your message to the team. Minister Sharma is currently reviewing the proposal and will need about 2 more weeks. He'd like to schedule a call with you on April 1st at 11 AM — does that work for you?
```

**Owner checks messages:**
```
Owner: /summary
Bot:   Today's Messages from Contacts:
       - priya_j: Hi, wanted to follow up on the JV proposal
       - ravi_k: Regarding tomorrow's meeting, can we push it to 4pm?
```

**Owner asks free-text:**
```
Owner: What did Ravi want?
Bot:   Ravi messaged today asking if the meeting scheduled for tomorrow can be pushed to 4 PM. No specific instructions were configured for him, so the bot replied with a standard message.
```

**Contact with no instructions:**
```
Unknown: Hi, is this the right number for appointments?
Bot:   Hello! This is Minister Sharma's office. I'm their personal assistant. Could you please share your name and how I can help you? I'll ensure your message reaches the right person.
```

---

## How Contact Matching Works

When a contact sends a message, the bot checks `pa_instructions` for their Telegram username. Matching is case-insensitive and partial:
- Contact username: `ravi_kumar` → matches instruction name `Ravi`
- Contact username: `priya` → matches instruction name `Priya Mehta`

**Tip:** Use first names in `/add` commands to match most Telegram usernames.

---

## No Pinecone Needed

This vertical is entirely instruction-based. The LLM uses the stored instructions as context — no vector search required. This makes it the simplest architecture of all 4 bots.

---

## File Structure

```
01-personal-agent/
├── bot.py          ← All logic: Telegram + Groq + Supabase (no agent.py needed)
├── prompts.py      ← System prompts for secretary and owner modes
├── .env.example
└── requirements.txt
```
