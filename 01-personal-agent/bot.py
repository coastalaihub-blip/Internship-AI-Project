"""
01-personal-agent/bot.py
Personal Secretary Bot — Owner pre-configures contacts; bot acts as secretary

Owner commands:
  /add <Name> "<instructions>"  → store contact instructions
  /list                         → show all active instructions
  /remove <Name>                → deactivate instructions for a contact
  /summary                      → today's contact message summary
  Free text                     → owner asks questions about their contacts

Contacts (everyone else):
  Regular messages              → bot responds using stored instructions for them

Run: python bot.py
"""

import os
import json
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client
from groq import Groq
from prompts import SECRETARY_SYSTEM_PROMPT, OWNER_SYSTEM_PROMPT

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
OWNER_TELEGRAM_ID = os.environ["OWNER_TELEGRAM_ID"]
OWNER_NAME = os.getenv("OWNER_NAME", "The Owner")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

_history: dict[str, list] = {}


def is_owner(user_id) -> bool:
    return str(user_id) == str(OWNER_TELEGRAM_ID)


def get_history(user_id: str) -> list:
    return _history.get(str(user_id), [])


def update_history(user_id: str, user_msg: str, bot_msg: str) -> None:
    history = _history.setdefault(str(user_id), [])
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": bot_msg})
    _history[str(user_id)] = history[-10:]


def log_conversation(user_id: str, username: str, user_msg: str, bot_msg: str, intent: str) -> None:
    try:
        supabase.table("conversations").insert({
            "bot_id": "personal_agent",
            "telegram_user_id": str(user_id),
            "telegram_username": username or "",
            "user_message": user_msg,
            "bot_response": bot_msg,
            "intent": intent
        }).execute()
    except Exception as e:
        print(f"Supabase log error: {e}")


def get_instructions_for_contact(contact_name: str) -> str:
    """Fetch active instructions for a contact by name (fuzzy match)."""
    try:
        result = supabase.table("pa_instructions").select("*").eq("is_active", True).execute()
        instructions = result.data or []
        # Case-insensitive partial match
        for inst in instructions:
            if contact_name.lower() in inst["contact_name"].lower() or inst["contact_name"].lower() in contact_name.lower():
                return inst["contact_context"]
        return ""
    except Exception as e:
        print(f"Supabase fetch error: {e}")
        return ""


def get_all_instructions() -> list:
    """Fetch all active instructions (for owner's /list and context)."""
    try:
        result = supabase.table("pa_instructions").select("*").eq("is_active", True).order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Supabase fetch error: {e}")
        return []


def get_today_summary() -> str:
    """Summarise today's contact messages from conversations table."""
    try:
        from datetime import date
        today = date.today().isoformat()
        result = supabase.table("conversations")\
            .select("telegram_username, user_message, created_at")\
            .eq("bot_id", "personal_agent")\
            .gte("created_at", f"{today}T00:00:00")\
            .neq("telegram_user_id", str(OWNER_TELEGRAM_ID))\
            .order("created_at", desc=False)\
            .execute()
        messages = result.data or []
        if not messages:
            return "No messages from contacts today."
        lines = []
        for msg in messages:
            username = msg.get("telegram_username") or "Unknown"
            text = msg.get("user_message", "")[:100]
            lines.append(f"- {username}: {text}")
        return "\n".join(lines)
    except Exception as e:
        print(f"Supabase summary error: {e}")
        return "Could not fetch today's messages."


def call_llm_json(messages: list) -> dict:
    """Call Groq and return parsed JSON."""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=400,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Groq error: {e}")
        return {
            "text": "I'm facing a technical issue. Please try again shortly.",
            "intent": "unknown",
            "action": "null",
            "action_data": None,
            "escalate": False
        }


# ── Owner Commands ────────────────────────────────────────────────────────────

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usage: /add Ravi "He's asking about the budget meeting. Offer Thursday 2pm or Friday 10am." """
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("Sorry, this command is only for the bot owner.")
        return

    text = update.message.text.replace("/add", "", 1).strip()
    # Parse: first word = name, rest in quotes = instructions
    match = re.match(r'^(\S+)\s+"(.+)"$', text, re.DOTALL)
    if not match:
        match = re.match(r"^(\S+)\s+'(.+)'$", text, re.DOTALL)
    if not match:
        await update.message.reply_text(
            'Usage: /add <Name> "<instructions>"\n\nExample:\n/add Ravi "He is asking about the budget meeting. Offer Thursday 2pm or Friday 10am."'
        )
        return

    contact_name = match.group(1)
    instructions = match.group(2)

    try:
        # Deactivate any existing instruction for this contact
        supabase.table("pa_instructions")\
            .update({"is_active": False})\
            .ilike("contact_name", contact_name)\
            .execute()

        # Insert new instruction
        supabase.table("pa_instructions").insert({
            "contact_name": contact_name,
            "contact_context": instructions,
            "is_active": True
        }).execute()

        await update.message.reply_text(f"Done. Instructions saved for {contact_name}.")
    except Exception as e:
        await update.message.reply_text(f"Error saving instructions: {e}")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("Sorry, this command is only for the bot owner.")
        return

    instructions = get_all_instructions()
    if not instructions:
        await update.message.reply_text("No active contact instructions. Use /add to add some.")
        return

    lines = ["*Active Contact Instructions:*\n"]
    for inst in instructions:
        lines.append(f"*{inst['contact_name']}*\n_{inst['contact_context']}_\n")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("Sorry, this command is only for the bot owner.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /remove <Name>")
        return

    contact_name = args[0]
    try:
        supabase.table("pa_instructions")\
            .update({"is_active": False})\
            .ilike("contact_name", contact_name)\
            .execute()
        await update.message.reply_text(f"Instructions for {contact_name} removed.")
    except Exception as e:
        await update.message.reply_text(f"Error removing: {e}")


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("Sorry, this command is only for the bot owner.")
        return

    summary = get_today_summary()
    await update.message.reply_text(f"*Today's Messages from Contacts:*\n\n{summary}", parse_mode="Markdown")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_owner(update.effective_user.id):
        await update.message.reply_text(
            f"Welcome, {OWNER_NAME}! I'm your personal AI secretary.\n\n"
            "Commands:\n"
            '/add <Name> "<instructions>" — Set how to handle a contact\n'
            "/list — See all contact instructions\n"
            "/remove <Name> — Remove a contact's instructions\n"
            "/summary — Today's contact message summary\n\n"
            "Or ask me anything: 'Who messaged today?' 'What did Ravi say?'"
        )
    else:
        await update.message.reply_text(
            f"Hello! You've reached {OWNER_NAME}'s office. I'm their personal assistant. How may I help you today?"
        )


# ── Message Handlers ──────────────────────────────────────────────────────────

async def handle_owner_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text messages from owner (queries about contacts, etc.)."""
    user_id = str(update.effective_user.id)
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    all_instructions = get_all_instructions()
    instructions_text = "\n".join([
        f"- {i['contact_name']}: {i['contact_context']}"
        for i in all_instructions
    ]) or "No contact instructions configured yet."

    today_summary = get_today_summary()
    system = OWNER_SYSTEM_PROMPT.format(
        owner_name=OWNER_NAME,
        all_instructions=instructions_text,
        contact_summary=today_summary,
        owner_query=user_message
    )

    response = call_llm_json([
        {"role": "system", "content": system},
        {"role": "user", "content": user_message}
    ])

    bot_text = response.get("text", "I couldn't process that query.")
    await update.message.reply_text(bot_text)
    log_conversation(user_id, OWNER_NAME, user_message, bot_text, response.get("intent", "unknown"))


async def handle_contact_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages from contacts (non-owner users)."""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or "Contact"
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Look up instructions for this contact (by their Telegram name)
    contact_instructions = get_instructions_for_contact(username)
    history = get_history(user_id)
    history_text = "\n".join([
        f"{'Contact' if m['role'] == 'user' else 'Secretary'}: {m['content']}"
        for m in history
    ]) or "No previous messages."

    system = SECRETARY_SYSTEM_PROMPT.format(
        owner_name=OWNER_NAME,
        contact_instructions=contact_instructions if contact_instructions else "No specific instructions. Respond as a general secretary.",
        history=history_text
    )

    response = call_llm_json([
        {"role": "system", "content": system},
        {"role": "user", "content": user_message}
    ])

    bot_text = response.get("text", f"Thank you for your message. I'll pass it along to {OWNER_NAME}.")
    await update.message.reply_text(bot_text)

    update_history(user_id, user_message, bot_text)
    log_conversation(user_id, username, user_message, bot_text, response.get("intent", "unknown"))


async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route message to owner handler or contact handler."""
    if is_owner(update.effective_user.id):
        await handle_owner_message(update, context)
    else:
        await handle_contact_message(update, context)


def main() -> None:
    print(f"Starting {OWNER_NAME}'s Personal Secretary Bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("remove", remove_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_message))

    print("Bot started. Polling for messages... (Ctrl+C to stop)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
