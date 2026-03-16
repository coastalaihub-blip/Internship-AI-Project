# Dashboard

A zero-build HTML dashboard showing real-time conversations and actions from all 4 bots.

---

## Setup (2 minutes)

1. Open `dashboard/app.js`
2. Paste your Supabase credentials at the top:
   ```js
   const SUPABASE_URL = "https://your-project.supabase.co";
   const SUPABASE_ANON_KEY = "eyJhbGci...";
   ```
3. Open `index.html` in your browser — or in Firebase Studio, right-click → **Preview**

That's it. No build step, no npm install.

---

## Features

### Stats Bar (top)
Real-time counts updated on every new message:
- **Messages Today** — total conversations across all bots
- **Appointments Today** — records in `appointments` table
- **Food Orders Today** — records in `food_orders` table
- **Escalations Today** — conversations where `intent = 'escalate'`

### Live Conversation Feed (left panel)
- Shows last 50 conversations, newest first
- Filter by bot using the dropdown
- **Realtime** — new messages appear instantly without refresh
- New messages flash blue briefly

Each conversation card shows:
- Bot tag (color-coded by vertical)
- Telegram username
- Intent tag
- User message + bot response

### Actions Log (right panel)
Combined view of all actions taken by bots:
- Clinic appointments
- Hotel room bookings
- Food orders

---

## Bot Color Coding

| Bot | Color |
|-----|-------|
| Personal Agent | Purple |
| Receptionist | Green |
| Call Center | Blue |
| Hotel | Amber |

---

## Files

```
dashboard/
├── index.html    ← Single page app
├── app.js        ← Supabase queries + realtime + rendering
├── style.css     ← Dark theme styles
└── .env.example  ← Reminder to paste credentials in app.js
```
