# 03 — Call Center Agent Bot

An AI customer support agent handling complaints, refunds, order queries, technical support, and escalation routing. Uses Pinecone for FAQ retrieval and Supabase for logging.

---

## What It Does

- Answers customer support FAQs via Pinecone RAG
- Handles: orders, refunds, returns, complaints, account issues, billing queries
- Logs complaints with urgency classification
- Escalates to human agents when needed
- Logs every conversation to Supabase

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

**Order Tracking:**
```
User: Where is my order? It's been 5 days.
Bot:  I understand your concern. Standard delivery takes 3-5 business days. You can track your order by entering your Order ID on our website. Could you share your Order ID so I can help further?
```

**Refund Query:**
```
User: I returned a product 10 days ago but haven't got my refund
Bot:  I'm sorry for the delay. Once a return is verified, refund is processed in 5-7 business days. Let me escalate this to our finance team right away.
🔔 I'm transferring you to a senior support agent. Please hold — average wait is 2-3 minutes.
```

**Damaged Product:**
```
User: I received a broken laptop
Bot:  I sincerely apologise for this. Please take photos of the damaged item and packaging. I'm logging this as a high-priority complaint and will arrange a replacement pickup within 48 hours.
```

**Escalation:**
```
User: This is ridiculous, I want to speak to a manager
Bot:  I completely understand your frustration and I'm sorry for the trouble. I'm connecting you to a senior agent right now.
🔔 I'm transferring you to a senior support agent. Please hold — average wait is 2-3 minutes.
```

**General FAQ:**
```
User: Do you accept EMI?
Bot:  Yes! EMI is available on purchases above ₹3000 using credit cards from SBI, HDFC, ICICI, Axis, and Kotak. Select 'Pay via EMI' at checkout for 3, 6, 9, or 12 month options.
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | List capabilities |

---

## Complaint Logging

When the LLM detects a complaint, it logs to Supabase `conversations` with:
- `intent = 'complaint'`
- `action_taken = 'log_complaint'`
- `user_message` prefixed with `[COMPLAINT]`

This makes complaints easily filterable in the dashboard.

---

## File Structure

```
03-call-center/
├── bot.py
├── agent.py
├── prompts.py
├── knowledge/
│   ├── faqs.json         ← 25 customer support FAQs
│   └── upload_faqs.py
├── .env.example
└── requirements.txt
```
