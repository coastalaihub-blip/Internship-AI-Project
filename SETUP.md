# Setup Guide — Internship AI Project

Get your Telegram bot running in 10 minutes. Follow each step in order.

---

## Prerequisites

- A Telegram account (phone number required)
- A Google account (for Firebase Studio + Groq)
- Your vertical folder (given by your team lead): `01`, `02`, `03`, or `04`

---

## Step 1 — Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Enter a display name: e.g. `Clinic Receptionist`
4. Enter a username (must end in `bot`): e.g. `clinic_intern2_bot`
5. BotFather replies with your **bot token** — looks like: `7312345678:AAHfqkE...`
6. Copy this token. You'll paste it into `.env` as `TELEGRAM_BOT_TOKEN`

---

## Step 2 — Get Groq API Key (Free)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign in with Google
3. Click **API Keys** → **Create API Key**
4. Name it: `intern-project`
5. Copy the key (starts with `gsk_...`) → this is your `GROQ_API_KEY`

> Free tier: 30 requests/minute, 14,400 requests/day. More than enough.

---

## Step 3 — Create Supabase Project & Run Schema

> **Note:** If your team has already done this, skip to Step 3c.

**3a. Create project:**
1. Go to [app.supabase.com](https://app.supabase.com)
2. Click **New Project** → name it `internship-ai`
3. Set a database password (save it somewhere)
4. Choose region: `Southeast Asia (Singapore)`

**3b. Run schema SQL:**
1. In your Supabase project, click **SQL Editor** in the left sidebar
2. Click **New Query**
3. Open `shared/supabase_schema.sql` from this repo
4. Paste the entire contents into the editor
5. Click **Run** — you should see "Success. No rows returned"

**3c. Get your credentials:**
1. Go to **Settings → API** in your Supabase project
2. Copy **Project URL** → this is `SUPABASE_URL`
3. Copy **anon public** key → this is `SUPABASE_ANON_KEY`

---

## Step 4 — Get Pinecone API Key

> Personal Agent (01) doesn't use Pinecone. Skip to Step 5 if you're on that vertical.

Ask your team lead for:
- `PINECONE_API_KEY` — shared across all verticals
- Your namespace:
  - Receptionist (02): `biz_intern_receptionist`
  - Call Center (03): `biz_intern_callcenter`
  - Hotel (04): `biz_intern_hotel`

> Do NOT create a new Pinecone index. One index is shared by all verticals with separate namespaces.

---

## Step 5 — Open Project in Firebase Studio (Antigravity)

1. Go to [idx.google.com](https://idx.google.com)
2. Click **Import a repo**
3. Paste your GitHub repo URL
4. Studio clones the repo and opens a cloud IDE
5. Open a terminal at the bottom

---

## Step 6 — Configure Your Environment

In the terminal, navigate to your folder and set up `.env`:

```bash
# Navigate to your vertical (replace with your number)
cd 02-receptionist

# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
```

Now open `.env` and fill in your 4 keys:

```bash
TELEGRAM_BOT_TOKEN=7312345678:AAHfqkE...   # from Step 1
GROQ_API_KEY=gsk_...                        # from Step 2
SUPABASE_URL=https://xxx.supabase.co        # from Step 3c
SUPABASE_ANON_KEY=eyJhbGci...              # from Step 3c
PINECONE_API_KEY=pcsk_...                   # from Step 4 (not needed for 01)
```

---

## Step 7 — Upload FAQs to Pinecone (One-time)

> Skip if you're on `01-personal-agent`.

```bash
# From inside your vertical folder
python knowledge/upload_faqs.py
```

You should see: `Uploaded 25 FAQs to namespace biz_intern_...`

> Only do this once. Running it again will re-upload (harmless but wasteful).

---

## Step 8 — Run Your Bot

```bash
python bot.py
```

You should see:
```
Bot started. Polling for messages...
```

Open Telegram → search for your bot username → send `/start`

---

## Step 9 — Test Your Bot

Try these messages based on your vertical:

**02-receptionist:**
- "What are your working hours?"
- "I want to book an appointment with Dr. Sharma for tomorrow"
- "Do you accept insurance?"

**03-call-center:**
- "My order hasn't arrived"
- "I want a refund"
- "I need to speak to a manager"

**04-hotel-agent:**
- "I want to book a deluxe room for 2 nights"
- "Can I see the menu?"
- "What time is check-in?"

**01-personal-agent (owner commands):**
- `/add Ravi "He is asking about the budget meeting. Offer Thursday 2pm or Friday 10am."`
- `/list`
- `/summary`
- Then as a contact (different Telegram account): "Hi, I'm Ravi. Wanted to discuss the meeting."

---

## Step 10 — View Dashboard

```bash
# From repo root
open dashboard/index.html
```

Or in Firebase Studio, right-click `dashboard/index.html` → **Preview**.

First time: open `dashboard/app.js` and paste your `SUPABASE_URL` and `SUPABASE_ANON_KEY` at the top.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Bot doesn't respond | Check `TELEGRAM_BOT_TOKEN` in `.env` — no spaces, no quotes |
| `AuthenticationError` from Groq | Check `GROQ_API_KEY` — must start with `gsk_` |
| Pinecone error | Run `python knowledge/upload_faqs.py` first |
| Supabase 401 error | Use `anon public` key (not `service_role`) for `SUPABASE_ANON_KEY` |
| Bot responds but doesn't book | Check Supabase table names match `shared/supabase_schema.sql` |

---

## Getting Help

1. Check `shared/docs/architecture.md` to understand the system
2. Ask your team lead
3. Check Groq docs: [console.groq.com/docs](https://console.groq.com/docs)
4. Check python-telegram-bot docs: [docs.python-telegram-bot.org](https://docs.python-telegram-bot.org)
