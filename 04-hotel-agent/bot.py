"""
04-hotel-agent/bot.py
Hotel & Restaurant Bot — Room booking + food orders (dual-mode agent)

Run: python bot.py
"""

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client
import agent
from prompts import GREETING_RESPONSE, MENU, ROOM_RATES

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
HOTEL_NAME = os.getenv("HOTEL_NAME", "Grand Mahal Hotel")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

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
            "bot_id": "hotel",
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
    """Write booking or food order to Supabase."""
    action = response.get("action", "null")
    data = response.get("action_data")

    if action == "book_room" and data:
        try:
            supabase.table("hotel_bookings").insert({
                "guest_name": data.get("guest_name", "Not provided"),
                "room_type": data.get("room_type", "standard"),
                "check_in": data.get("check_in"),
                "check_out": data.get("check_out"),
                "guests_count": data.get("guests_count", 1),
                "total_amount": data.get("total_amount"),
                "telegram_user_id": str(user_id)
            }).execute()
            print(f"Room booked for {data.get('guest_name')}: {data.get('room_type')}")
        except Exception as e:
            print(f"Supabase booking error: {e}")

    elif action == "place_order" and data:
        try:
            supabase.table("food_orders").insert({
                "customer_name": data.get("customer_name", "Guest"),
                "room_number": data.get("room_number", "Takeaway"),
                "items": data.get("items", []),
                "total_amount": data.get("total_amount"),
                "status": "pending",
                "telegram_user_id": str(user_id)
            }).execute()
            print(f"Food order placed: {data.get('items')}")
        except Exception as e:
            print(f"Supabase order error: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    greeting = GREETING_RESPONSE["text"].format(hotel_name=HOTEL_NAME)
    await update.message.reply_text(greeting)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"*{HOTEL_NAME} — Restaurant Menu*\n{MENU}",
        parse_mode="Markdown"
    )


async def rooms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"*{HOTEL_NAME} — Rooms & Rates*\n{ROOM_RATES}\n\nTo book, just say: 'I want to book a deluxe room for 2 nights from March 20'",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        f"*{HOTEL_NAME} — AI Concierge*\n\n"
        "I can help you with:\n"
        "• 🛏️ Room booking\n"
        "• 🍽️ Food & room service orders\n"
        "• ℹ️ Hotel information & policies\n\n"
        "Quick commands:\n"
        "/menu — View restaurant menu\n"
        "/rooms — View room types & rates\n\n"
        "_Examples:_\n"
        "_'Book a deluxe room for 2 nights from Friday'_\n"
        "_'I want 2 Butter Chicken and 1 Dal Makhani to room 304'_\n"
        "_'What time is check-out?'_"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or ""
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    history = get_history(user_id)
    response = agent.get_response(user_message, history)

    bot_text = response.get("text", "I beg your pardon, could you please repeat that?")
    intent = response.get("intent", "unknown")
    action = response.get("action", "null")

    if response.get("escalate", False):
        bot_text += "\n\n🔔 I'm connecting you with our front desk. Please hold on."

    await update.message.reply_text(bot_text)

    update_history(user_id, user_message, bot_text)
    log_conversation(user_id, username, user_message, bot_text, intent, action)
    handle_action(user_id, response)


def main() -> None:
    print(f"Starting {HOTEL_NAME} Bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("rooms", rooms_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started. Polling for messages... (Ctrl+C to stop)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
