"""
03-call-center/bot.py
Call Center Agent Bot — Customer support, complaint resolution, FAQ, escalation

Run: python bot.py
"""

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client
import agent
from prompts import GREETING_RESPONSE

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
COMPANY_NAME = os.getenv("COMPANY_NAME", "TechMart India")

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
    try:
        supabase.table("conversations").insert({
            "bot_id": "call_center",
            "telegram_user_id": str(user_id),
            "telegram_username": username or "",
            "user_message": user_msg,
            "bot_response": bot_msg,
            "intent": intent,
            "action_taken": action if action != "null" else None
        }).execute()
    except Exception as e:
        print(f"Supabase log error: {e}")


def handle_action(user_id: str, username: str, response: dict) -> None:
    """Log complaints to Supabase conversations with extra context."""
    action = response.get("action", "null")
    data = response.get("action_data")

    if action == "log_complaint" and data:
        # Log complaint as a special conversation entry
        try:
            supabase.table("conversations").insert({
                "bot_id": "call_center",
                "telegram_user_id": str(user_id),
                "telegram_username": username or "",
                "user_message": f"[COMPLAINT] {data.get('description', '')}",
                "bot_response": f"Complaint logged: {data.get('complaint_type', 'other')} | Urgency: {data.get('urgency', 'medium')}",
                "intent": "complaint",
                "action_taken": "log_complaint"
            }).execute()
            print(f"Complaint logged for user {user_id}: {data.get('complaint_type')}")
        except Exception as e:
            print(f"Supabase complaint log error: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    greeting = GREETING_RESPONSE["text"].format(company_name=COMPANY_NAME)
    await update.message.reply_text(greeting)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        f"*{COMPANY_NAME} — Customer Support*\n\n"
        "I can help you with:\n"
        "• 📦 Order tracking & delivery issues\n"
        "• 💰 Refunds & returns\n"
        "• 🔧 Technical support\n"
        "• 📋 Complaints & escalations\n"
        "• 🏪 Account management\n"
        "• ❓ General product queries\n\n"
        "Just describe your issue and I'll help resolve it!\n\n"
        "_Example: 'My order #12345 hasn't been delivered'_"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or ""
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    history = get_history(user_id)
    response = agent.get_response(user_message, history)

    bot_text = response.get("text", "I'm sorry, could you please repeat your query?")
    intent = response.get("intent", "unknown")
    action = response.get("action", "null")

    if response.get("escalate", False):
        bot_text += "\n\n🔔 I'm transferring you to a senior support agent. Please hold — average wait is 2-3 minutes."

    await update.message.reply_text(bot_text)

    update_history(user_id, user_message, bot_text)
    log_conversation(user_id, username, user_message, bot_text, intent, action)
    handle_action(user_id, username, response)


def main() -> None:
    print(f"Starting {COMPANY_NAME} Call Center Bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started. Polling for messages... (Ctrl+C to stop)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
