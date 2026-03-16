# Intern User Manual — Internship AI Project

> **The only document you need to go from zero to a running Telegram bot.**
> Read each section before you act. Every API key is created by YOU — nothing is pre-filled.

---

## 1. What Is This Project?

You are building one of **four Telegram-based AI bots** — each representing a real-world business vertical. The bots use:

- **Groq** (free LLM — llama-3.3-70b-versatile) — the "brain"
- **Pinecone** (vector database) — stores FAQ answers so the bot can look them up by meaning
- **Supabase** (PostgreSQL) — logs every conversation, booking, and order
- **python-telegram-bot** — connects everything to Telegram

### Quick-Reference: Who Builds What

| Intern | Vertical | Folder | Bot Persona |
|--------|----------|--------|-------------|
| Intern 1 | Personal Secretary | `01-personal-agent` | Private assistant (no Pinecone) |
| Intern 2 | Business Receptionist | `02-receptionist` | Clinic front desk |
| Intern 3 | Call Center Agent | `03-call-center` | Tech support line |
| Intern 4 | Hotel & Restaurant Agent | `04-hotel-agent` | Hotel concierge |

### Every Key Is Your Own

There are no pre-filled credentials in any `.env` file. Every intern creates their own accounts and fills every key themselves. This means:

- Your bot is fully under your control
- Your data is in your own Supabase project and Pinecone index
- You learn the full setup end-to-end

---

## 2. Accounts to Create (One-Time, All Free)

Create all accounts for your vertical before starting. Each takes under 3 minutes.

| # | Account | Used for | URL |
|---|---------|----------|-----|
| 1 | Telegram | Run and test the bot | https://telegram.org |
| 2 | Groq | Free LLM inference | https://console.groq.com |
| 3 | Supabase | Database for logs | https://supabase.com |
| 4 | Pinecone | FAQ vector store (02, 03, 04) | https://pinecone.io |
| 5 | GitHub | Clone the repo | https://github.com |
| 6 | Firebase Studio (optional) | Cloud IDE | https://idx.google.com |

> **Groq free tier:** 30 requests/minute, 14,400/day — more than enough for this project.

---

## 3. Step-by-Step: Get Your API Keys

### A. TELEGRAM_BOT_TOKEN (every intern)

1. Open Telegram → search **@BotFather** (official, blue checkmark)
2. Send `/newbot`
3. Enter a display name (e.g., `City Clinic Bot`)
4. Enter a username — **must end in `bot`** (e.g., `cityclinic_yourname_bot`)
5. BotFather replies with your token:
   ```
   1234567890:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. Paste it into your `.env` as `TELEGRAM_BOT_TOKEN=`

> Never share this token. Anyone who has it can control your bot.

---

### B. GROQ_API_KEY (every intern)

1. Go to https://console.groq.com → Sign in with Google
2. Navigate to **API Keys** → **Create API Key**
3. Name it `intern-project` → copy the key (starts with `gsk_`)
4. Paste into your `.env` as `GROQ_API_KEY=`

---

### C. SUPABASE_URL + SUPABASE_ANON_KEY (every intern)

You need your own Supabase project so your bot can log data.

1. Go to https://supabase.com → **Sign up free**
2. Click **New project** → choose a name and strong password → wait ~1 minute for provisioning
3. Go to **SQL Editor** (left sidebar)
4. Open `shared/supabase_schema.sql` from this repo → copy the entire contents → paste into the SQL Editor → click **Run**
   - This creates all the tables: `messages`, `appointments`, `complaints`, `bookings`, `orders`
5. Go to **Settings → API**
   - Copy **Project URL** → paste as `SUPABASE_URL=`
   - Copy **anon public** key → paste as `SUPABASE_ANON_KEY=`

> Use the **anon** key (not `service_role`). The anon key is safe for bots.

---

### D. PINECONE_API_KEY + Index Setup (interns 2, 3, 4 only)

Intern 1 (`01-personal-agent`) does not use Pinecone — skip this step.

1. Go to https://pinecone.io → **Sign up free**
2. Click **Create index**:
   - **Index name:** `ai-agent-platform`
   - **Model:** `llama-text-embed-v2`
   - **Dimensions:** `1024`
   - **Cloud:** `AWS` / **Region:** `us-east-1`
   - Click **Create**
3. Go to **API Keys** tab → copy your key (starts with `pcsk_`)
4. Paste into your `.env`:
   - `PINECONE_API_KEY=` ← your key
   - `PINECONE_INDEX_NAME=ai-agent-platform` ← must match exactly what you named it
   - `PINECONE_NAMESPACE=` ← see your vertical's section below for the value to use

> After creating the index, run `python knowledge/upload_faqs.py` once to push your FAQs in.

---

### E. OWNER_TELEGRAM_ID (Intern 1 only)

1. Open Telegram → search **@userinfobot**
2. Send any message (e.g., `/start`)
3. It replies with your numeric ID, e.g., `Your id: 987654321`
4. Paste into `.env` as `OWNER_TELEGRAM_ID=987654321`

> Must be a plain number — no quotes, no spaces.

---

## 4. Editing FAQs

For verticals 02, 03, and 04, your bot's answers come from a JSON file you can edit freely.

### Where the FAQ files live

| Vertical | FAQ file |
|----------|----------|
| 02-receptionist | `02-receptionist/knowledge/faqs.json` |
| 03-call-center | `03-call-center/knowledge/faqs.json` |
| 04-hotel-agent | `04-hotel-agent/knowledge/faqs.json` |

### FAQ entry format

```json
{
  "id": "faq_001",
  "question": "What are your working hours?",
  "answer": "We are open Monday to Saturday, 9 AM to 7 PM.",
  "category": "hours",
  "tags": ["hours", "timing", "open", "close"]
}
```

### Rules for editing

- `id` must be unique across all entries (`faq_001`, `faq_002`, etc.)
- `question` should sound like how a real user would ask it
- `answer` is what the bot will say in response
- `category` and `tags` improve search accuracy — keep them relevant to the content
- 20–30 entries is a good range; add as many as your domain needs
- After any change to `faqs.json`, re-run the upload script to push the changes:
  ```bash
  python knowledge/upload_faqs.py
  ```
  This will overwrite existing entries in Pinecone with the updated versions.

> **Tip:** Make the FAQs specific to your own business idea. If you change the domain (e.g., from a clinic to a pharmacy), update `BIZ_NAME` in `.env` and edit the prompts in `prompts.py` to match.

---

## 5. Per-Vertical Setup Guide

Jump to your section. Do not skip steps.

---

### Intern 1 — Personal Secretary (`01-personal-agent`)

**What this bot does:** Acts as a private assistant for a named person. Handles notes, reminders, and task delegation. No Pinecone — no FAQ lookup.

**Your `.env` file** (`01-personal-agent/.env`):
```env
TELEGRAM_BOT_TOKEN=          ← Step A
GROQ_API_KEY=                ← Step B
SUPABASE_URL=                ← Step C
SUPABASE_ANON_KEY=           ← Step C
OWNER_TELEGRAM_ID=           ← Step E
OWNER_NAME=Your Name Here    ← change to your preferred name/persona
```

**Setup steps:**
```bash
cd /path/to/internship-ai-project
source .venv/bin/activate
cd 01-personal-agent
# Edit .env — fill all blank fields
python bot.py
```

**Test checklist:**
- [ ] Send `/start` → expect a welcome message using your `OWNER_NAME`
- [ ] Send "Remind me to call Ravi at 5pm" → expect a confirmation
- [ ] Send "What are my tasks today?" → expect a list or acknowledgement
- [ ] Check Supabase → `messages` table → expect a new row
- [ ] Send from a different Telegram account → bot should not respond (owner-only)

---

### Intern 2 — Business Receptionist (`02-receptionist`)

**What this bot does:** Answers patient questions, handles appointment bookings, looks up FAQs from Pinecone.

**Your `.env` file** (`02-receptionist/.env`):
```env
TELEGRAM_BOT_TOKEN=              ← Step A
GROQ_API_KEY=                    ← Step B
SUPABASE_URL=                    ← Step C
SUPABASE_ANON_KEY=               ← Step C
PINECONE_API_KEY=                ← Step D
PINECONE_INDEX_NAME=ai-agent-platform  ← Step D (must match index name exactly)
PINECONE_NAMESPACE=biz_intern_receptionist  ← keep this or use your own name
BIZ_NAME=City Clinic             ← change to your clinic name
```

**IMPORTANT — Run this FIRST (one-time only):**
```bash
cd /path/to/internship-ai-project
source .venv/bin/activate
cd 02-receptionist
python knowledge/upload_faqs.py    # uploads clinic FAQs to Pinecone
```

**Then start the bot:**
```bash
python bot.py
```

**Test checklist:**
- [ ] Send `/start` → expect a clinic welcome message
- [ ] Ask "What are your clinic hours?" → expect an answer from the FAQ
- [ ] Ask "I want to book an appointment for tomorrow" → expect a booking flow
- [ ] Check Supabase → `appointments` table → expect your booking logged
- [ ] Ask something off-topic (e.g., "Who won IPL?") → bot should politely redirect

---

### Intern 3 — Call Center Agent (`03-call-center`)

**What this bot does:** Handles customer support — answers product questions, logs complaints, escalates unresolved issues.

**Your `.env` file** (`03-call-center/.env`):
```env
TELEGRAM_BOT_TOKEN=              ← Step A
GROQ_API_KEY=                    ← Step B
SUPABASE_URL=                    ← Step C
SUPABASE_ANON_KEY=               ← Step C
PINECONE_API_KEY=                ← Step D
PINECONE_INDEX_NAME=ai-agent-platform  ← Step D (must match index name exactly)
PINECONE_NAMESPACE=biz_intern_callcenter  ← keep this or use your own name
COMPANY_NAME=TechMart India      ← change to your company name
```

**IMPORTANT — Run this FIRST (one-time only):**
```bash
cd /path/to/internship-ai-project
source .venv/bin/activate
cd 03-call-center
python knowledge/upload_faqs.py    # uploads call center FAQs to Pinecone
```

**Then start the bot:**
```bash
python bot.py
```

**Test checklist:**
- [ ] Send `/start` → expect a TechMart support welcome
- [ ] Ask "How do I return a product?" → expect a policy answer from FAQ
- [ ] Say "My order hasn't arrived in 10 days" → expect complaint logging flow
- [ ] Check Supabase → `complaints` table → expect a new row
- [ ] Say "I want to speak to a manager" → expect an escalation message

---

### Intern 4 — Hotel & Restaurant Agent (`04-hotel-agent`)

**What this bot does:** Handles room bookings and food orders. Has `/rooms` and `/menu` commands.

**Your `.env` file** (`04-hotel-agent/.env`):
```env
TELEGRAM_BOT_TOKEN=              ← Step A
GROQ_API_KEY=                    ← Step B
SUPABASE_URL=                    ← Step C
SUPABASE_ANON_KEY=               ← Step C
PINECONE_API_KEY=                ← Step D
PINECONE_INDEX_NAME=ai-agent-platform  ← Step D (must match index name exactly)
PINECONE_NAMESPACE=biz_intern_hotel  ← keep this or use your own name
HOTEL_NAME=Grand Mahal Hotel     ← change to your hotel name
```

**IMPORTANT — Run this FIRST (one-time only):**
```bash
cd /path/to/internship-ai-project
source .venv/bin/activate
cd 04-hotel-agent
python knowledge/upload_faqs.py    # uploads hotel FAQs to Pinecone
```

**Then start the bot:**
```bash
python bot.py
```

**Test checklist:**
- [ ] Send `/start` → expect a hotel welcome message
- [ ] Send `/rooms` → expect room types and prices
- [ ] Send `/menu` → expect the restaurant menu
- [ ] Say "I want to book a deluxe room for 2 nights from March 20" → expect a booking flow
- [ ] Say "Order 2 butter naans and 1 dal makhani" → expect a food order confirmation
- [ ] Check Supabase → `bookings` and `orders` tables → expect your entries logged

---

## 6. Running Your Bot (Universal Steps)

```bash
# Step 1: Go to the project root
cd /path/to/internship-ai-project

# Step 2: Activate the shared virtual environment
source .venv/bin/activate
# You should see (.venv) at the start of your terminal prompt

# Step 3: Go to your vertical folder
cd 02-receptionist   # or 01-personal-agent, 03-call-center, 04-hotel-agent

# Step 4 (02/03/04 only — first time): Upload FAQs
python knowledge/upload_faqs.py

# Step 5: Start the bot
python bot.py
```

**Expected output:**
```
Bot started. Polling for messages...
```

**To stop the bot:** Press `Ctrl + C`

**To keep it running after closing the terminal:**
```bash
nohup python bot.py &
```

---

## 7. Testing Checklist (per vertical)

After your bot is running, verify each of these:

**All verticals:**
- [ ] Fill `.env` with all keys → start `python bot.py` → no errors in terminal
- [ ] Send `/start` on Telegram → bot responds with correct persona
- [ ] Check Supabase `messages` table → row logged after each message

**Verticals 02, 03, 04 additionally:**
- [ ] Run `python knowledge/upload_faqs.py` → shows "Done! X FAQs uploaded"
- [ ] Ask a question covered in `faqs.json` → bot gives correct FAQ answer
- [ ] Edit one FAQ in `faqs.json` → re-run `upload_faqs.py` → ask the edited question → answer reflects the change

---

## 8. Dashboard Setup

The dashboard shows live stats across all bots in one browser view.

**Steps:**

1. Open `dashboard/app.js` in your editor
2. At the top of the file, paste **your own** Supabase credentials:
   ```javascript
   const SUPABASE_URL = "https://yourproject.supabase.co";
   const SUPABASE_ANON_KEY = "eyJhbGci...your-anon-key...";
   ```
3. Open `dashboard/index.html` directly in your browser
   - Or in Firebase Studio: open the file → click **Preview**

**What the dashboard shows:**
- Total messages across all bots
- Live conversation feed (last 20 messages)
- Bookings/orders/complaints count per vertical
- Actions log (who did what, when)

> Use the **anon** key in app.js — it is safe for browser JavaScript. Never use `service_role` here.

---

## 9. Troubleshooting

| Error / Symptom | Likely Cause | Fix |
|-----------------|--------------|-----|
| `ModuleNotFoundError: No module named 'telegram'` | Virtual env not active | Run `source .venv/bin/activate` first |
| Bot doesn't respond to messages | Wrong or missing token | Check `TELEGRAM_BOT_TOKEN` in `.env` — no spaces, no quotes |
| `AuthenticationError` or `401` from Groq | Bad API key | Check `GROQ_API_KEY` starts with `gsk_` and has no typos |
| `PineconeException` or connection error | FAQs not uploaded yet | Run `python knowledge/upload_faqs.py` first |
| Bot replies "I don't know" to every FAQ question | FAQs not in Pinecone | Run `python knowledge/upload_faqs.py` |
| `upload_faqs.py` fails: `PINECONE_API_KEY not set` | `.env` not filled | Add your Pinecone key to `.env` |
| `upload_faqs.py` fails: `index not found` | Index name mismatch | Check `PINECONE_INDEX_NAME` in `.env` matches exactly what you created in Pinecone |
| Supabase `401 Unauthorized` | Wrong key type | Use the **anon** key, not `service_role` |
| Supabase `403` or permission denied | Table not created | Re-run `shared/supabase_schema.sql` in Supabase SQL Editor |
| Bot stops responding after a while | Terminal closed | Use `nohup python bot.py &` |
| Dashboard shows "Configuration Required" | app.js not filled | Paste your Supabase URL + anon key into `dashboard/app.js` |
| `.env` changes not picked up | Old process running | Stop bot (`Ctrl+C`), restart `python bot.py` |

---

## 10. Quick Architecture (How a Message Flows)

```
You (Telegram user)
       │
       ▼
 Telegram servers
       │  (webhook / polling)
       ▼
 python-telegram-bot  ←── your bot.py
       │
       ├─► Groq API (llama-3.3-70b-versatile)
       │       └── generates the reply text
       │
       ├─► Pinecone (02, 03, 04 only)
       │       └── looks up relevant FAQs by meaning, not exact match
       │
       └─► Supabase (all bots)
               └── logs the conversation, booking, or order
```

**In plain English:**

1. You send a message on Telegram
2. `bot.py` receives it via polling (checks every second)
3. For FAQ bots (02–04): Pinecone finds the 3 closest matching FAQs and adds them to the LLM context
4. Groq generates a reply using the system prompt + FAQ context + conversation history
5. The reply is sent back to you on Telegram
6. The full conversation is logged in Supabase

---

## 11. Clone the Repo (First-Time Setup)

```bash
git clone https://github.com/coastalaihub-blip/Agent-Project internship-ai-project
cd internship-ai-project
```

**Important:**
- `.env` files are listed in `.gitignore` — they will not be cloned. You fill your own credentials locally.
- Never commit `.env` files to Git.
- The shared virtual environment is in `.venv/` at the root — activate it with `source .venv/bin/activate`

**To push your changes:**
```bash
git add .
git commit -m "Add: describe what you changed"
git push
```

---

## 12. Getting Help

**Check these first:**
- `shared/docs/architecture.md` — full system diagram and component explanations
- This file (INTERN_GUIDE.md) — comprehensive setup reference

**Official docs:**
- python-telegram-bot: https://docs.python-telegram-bot.org
- Groq API: https://console.groq.com/docs
- Pinecone: https://docs.pinecone.io
- Supabase: https://supabase.com/docs

**Escalate to team lead for:**
- Supabase schema errors (table creation failed)
- Pinecone index creation issues
- Questions about customizing bot behavior beyond `.env`

---

*Last updated: March 2026 — Internship AI Project*
