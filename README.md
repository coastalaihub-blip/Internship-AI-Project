# Internship AI Project

4 AI agents built on Telegram. Each intern owns one vertical. All agents use the same free stack: Groq (Llama 3.1 70B) + Pinecone + Supabase + Telegram Bot API.

---

## Interns & Verticals

| Intern | Vertical | Folder | Description |
|--------|----------|--------|-------------|
| Intern 1 | Personal Secretary | [01-personal-agent/](./01-personal-agent/) | Owner pre-configures contacts + instructions; bot acts as secretary for a busy professional |
| Intern 2 | Business Receptionist | [02-receptionist/](./02-receptionist/) | Clinic appointment booking + FAQ answering + escalation |
| Intern 3 | Call Center Agent | [03-call-center/](./03-call-center/) | Customer support, complaint resolution, FAQ, escalation routing |
| Intern 4 | Hotel & Restaurant | [04-hotel-agent/](./04-hotel-agent/) | Room booking + food order taking (dual-mode agent) |

---

## Quick Start

→ Read [SETUP.md](./SETUP.md) — complete onboarding guide (10 minutes from zero to running bot)

→ Shared dashboard: [dashboard/](./dashboard/) — real-time view of all bot conversations

---

## Architecture

```
Telegram User
     ↓  (text message)
python-telegram-bot 21.x  (polling — no server/URL needed)
     ↓
In-memory conversation history (last 5 exchanges per user)
     ↓
Groq API → llama-3.1-70b-versatile  (free: 30 req/min, 14.4K/day)
     ↓  (for verticals with FAQs)
Pinecone search_records() → top-3 FAQ chunks
     ↓
Parse LLM JSON → take action (book / order / configure)
     ↓
Supabase → log conversation + write action record
```

---

## Shared Infrastructure

| Resource | Who manages | Notes |
|----------|-------------|-------|
| Supabase project | Team owner | Run `shared/supabase_schema.sql` once in SQL editor |
| Pinecone index | Team owner | Shared `PINECONE_API_KEY`, separate namespace per vertical |
| Telegram bot tokens | Each intern | @BotFather → `/newbot` |
| Groq API key | Each intern | console.groq.com → free signup |

---

## Tech Stack

| Component | Tool |
|-----------|------|
| Telegram bot | python-telegram-bot 21.x (polling) |
| LLM | Groq — llama-3.1-70b-versatile (free tier) |
| Vector DB | Pinecone free tier (serverless, llama-text-embed-v2) |
| Database | Supabase (free tier) |
| Dashboard | Vanilla HTML + Supabase JS CDN |
| Editor | Firebase Studio / Google IDX (cloud IDE) |

---

## Repo Structure

```
internship-ai-project/
├── README.md
├── SETUP.md
├── .gitignore
├── .idx/dev.nix                  ← Firebase Studio / Antigravity config
├── shared/
│   ├── supabase_schema.sql       ← Run once in Supabase SQL editor
│   └── docs/
│       ├── architecture.md
│       └── faq_format.md
├── 01-personal-agent/
├── 02-receptionist/
├── 03-call-center/
├── 04-hotel-agent/
└── dashboard/
```
