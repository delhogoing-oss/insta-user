
import logging
import random
import string
import os
import time
import hmac
import hashlib
import base64
import struct

from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.error import TelegramError
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================

load_dotenv(Path(__file__).parent / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DEFAULT_PASSWORD = "0plm0plm"


# =========================
# USERNAME GENERATOR
# =========================

def generate_username():
    names = [
        "aayan", "vihaan", "rudra", "atharv", "shivansh", "arnav",
        "lakshya", "vedant", "madhav", "keshav", "advait", "nikhil",
        "harsh", "omkar", "samar", "pranav", "riya", "kiara",
        "isha", "tanvi", "meera", "kavya", "navya", "prisha",
        "ethan", "mason", "logan", "jack", "owen", "aiden",
        "caleb", "samuel", "daniel", "matthew", "joseph",
        "david", "andrew", "julian"
    ]

    name = random.choice(names)
    name_part = name[:random.randint(3, len(name))]
    numbers = str(random.randint(99, 999))
    letters = "".join(random.choices(string.ascii_lowercase, k=2))

    return f"{name_part}{numbers}_{letters}"


# =========================
# TOTP GENERATOR
# =========================

def get_hotp_token(secret, intervals_no):
    secret = secret.strip().replace(" ", "").upper()

    key = base64.b32decode(secret, casefold=True)
    msg = struct.pack(">Q", intervals_no)

    digest = hmac.new(key, msg, hashlib.sha1).digest()

    offset = digest[19] & 0x0F
    binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF

    otp = binary % 1000000
    return str(otp).zfill(6)


def get_totp_token(secret):
    interval = int(time.time()) // 30
    return get_hotp_token(secret, interval)


# =========================
# DELETE MESSAGE
# =========================

async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job

    if not job:
        return

    chat_id = job.data.get("chat_id")
    message_id = job.data.get("message_id")

    try:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
    except TelegramError:
        logger.debug("Message deletion failed or message already deleted")


def schedule_delete(context, chat_id, message_id, seconds=60):
    if context.job_queue:
        context.job_queue.run_once(
            delete_message,
            when=seconds,
            data={
                "chat_id": chat_id,
                "message_id": message_id
            }
        )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(
            "🎯 GENERATE USERNAME",
            callback_data="generate"
        )]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🤖 *Username Generator*\n\n"
        "Tap the button below to generate a username.\n\n"
        "*Commands:*\n"
        "/gen - Quick generation\n"
        "/setpassword <password> - Set your password",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


# =========================
# BUTTON GENERATOR
# =========================

async def generate_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    username = generate_username()
    password = context.user_data.get("password", DEFAULT_PASSWORD)

    message = (
        "✅ *Generated successfully*\n\n"
        f"Username = `{username}`\n\n"
        "━━━━━━━━━━━━\n"
        f"Password = `{password}`\n"
        "━━━━━━━━━━━━"
    )

    keyboard = [
        [InlineKeyboardButton(
            "🔄 GENERATE ANOTHER",
            callback_data="generate"
        )]
    ]

    await query.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# QUICK GENERATE
# =========================

async def quick_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    username = generate_username()
    password = context.user_data.get("password", DEFAULT_PASSWORD)

    await update.message.reply_text(
        "⚡ *Quick Generate*\n\n"
        f"Username: `{username}`\n"
        f"Password: `{password}`\n\n"
        "📋 Tap and hold to copy",
        parse_mode="Markdown",
    )


# =========================
# SET PASSWORD
# =========================

async def set_password(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not context.args:
        await update.message.reply_text(
            "❌ Usage:\n/setpassword your-password"
        )
        return

    password = " ".join(context.args)

    context.user_data["password"] = password

    await update.message.reply_text(
        "✅ Custom password updated successfully."
    )


# =========================
# OTP MESSAGE HANDLER
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    secret = update.message.text.strip().replace(" ", "").upper()

    try:
        otp = get_totp_token(secret)

        sent_message = await update.message.reply_text(
            f"🔐 Your OTP: `{otp}`\n\n"
            "⏳ Valid for approximately 30 seconds.",
            parse_mode="Markdown",
        )

        schedule_delete(
            context,
            sent_message.chat_id,
            sent_message.message_id,
            seconds=60,
        )

        # Remove the message containing the secret, if possible.
        try:
            await update.message.delete()
        except TelegramError:
            pass

    except Exception:
        await update.message.reply_text(
            "❌ Invalid authenticator key. Please check it and try again."
        )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    logger.error(
        "Bot error while processing update",
        exc_info=context.error
    )


# =========================
# STARTUP: REMOVE WEBHOOK
# =========================

async def post_init(application: Application):
    await application.bot.delete_webhook(
        drop_pending_updates=False
    )
    logger.info("Webhook removed. Polling is ready.")


# =========================
# MAIN
# =========================

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found!")
        print("Add BOT_TOKEN in Railway Variables or .env")
        return

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", quick_command))
    app.add_handler(CommandHandler("setpassword", set_password))

    app.add_handler(
        CallbackQueryHandler(
            generate_handler,
            pattern="^generate$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.add_error_handler(error_handler)

    logger.info("🤖 Bot starting in polling mode...")

    app.run_polling(
        drop_pending_updates=False
    )


if __name__ == "__main__":
    main()
