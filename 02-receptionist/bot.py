"""
02-receptionist/bot.py
Business Receptionist Bot — Clinic appointment booking + FAQ answering

Run: python bot.py
"""

import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import agent
from prompts import GREETING_RESPONSE

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
BIZ_NAME = os.getenv("BIZ_NAME", "City Clinic")

# Supabase is optional — logging is skipped if not configured
supabase = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# In-memory conversation history: user_id → last 10 messages (5 exchanges)
_history: dict[str, list] = {}


def get_history(user_id: str) -> list:
    return _history.get(str(user_id), [])


def update_history(user_id: str, user_msg: str, bot_msg: str) -> None:
    history = _history.setdefault(str(user_id), [])
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": bot_msg})
    _history[str(user_id)] = history[-10:]


def log_conversation(user_id: str, username: str, user_msg: str, bot_msg: str, intent: str, action: str) -> None:
    """Log conversation to Supabase (fire-and-forget, errors are non-fatal)."""
    if not supabase:
        return
    try:
        supabase.table("conversations").insert({
            "bot_id": "receptionist",
            "telegram_user_id": str(user_id),
            "telegram_username": username or "",
            "user_message": user_msg,
            "bot_response": bot_msg,
            "intent": intent,
            "action_taken": action if action != "null" else None
        }).execute()
    except Exception as e:
        print(f"Supabase log error: {e}")


def handle_action(user_id: str, response: dict) -> None:
    """Write action records to Supabase based on LLM response."""
    if not supabase:
        return
    action = response.get("action", "null")
    data = response.get("action_data")

    if action == "book_appointment" and data:
        try:
            supabase.table("appointments").insert({
                "patient_name": data.get("patient_name", "Not provided"),
                "phone": data.get("phone", "Not provided"),
                "appointment_datetime": data.get("appointment_datetime", "To be confirmed"),
                "doctor": data.get("doctor", "Any available doctor"),
                "notes": data.get("notes", ""),
                "telegram_user_id": str(user_id)
            }).execute()
            print(f"Appointment booked for {data.get('patient_name')}")
        except Exception as e:
            print(f"Supabase appointment error: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    greeting = GREETING_RESPONSE["text"].format(biz_name=BIZ_NAME)
    await update.message.reply_text(greeting)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        f"*{BIZ_NAME} — AI Receptionist*\n\n"
        "I can help you with:\n"
        "• 📅 Book an appointment\n"
        "• ❓ Answer clinic questions\n"
        "• 🏥 Doctor availability\n"
        "• 📞 Connect you with staff\n\n"
        "Just type your question or request naturally!\n\n"
        "_Example: 'I want to book an appointment with Dr. Sharma for Friday'_"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or ""
    user_message = update.message.text

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    history = get_history(user_id)
    response = agent.get_response(user_message, history)

    bot_text = response.get("text", "I'm sorry, could you please repeat that?")
    intent = response.get("intent", "unknown")
    action = response.get("action", "null")

    # Handle escalation
    if response.get("escalate", False):
        bot_text += "\n\n📞 I'm connecting you with our staff. Please hold on."

    await update.message.reply_text(bot_text)

    # Update memory and log
    update_history(user_id, user_message, bot_text)
    log_conversation(user_id, username, user_message, bot_text, intent, action)
    handle_action(user_id, response)


def main() -> None:
    print(f"Starting {BIZ_NAME} Receptionist Bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started. Polling for messages... (Ctrl+C to stop)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
