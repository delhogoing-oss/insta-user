import logging
import random
import string
import os
import time
import hmac
import hashlib
import base64
import struct
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

from pathlib import Path

# Load token directly from .env file to avoid environment variable conflicts
env_path = Path(__file__).parent / ".env"
BOT_TOKEN = None
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip().startswith('BOT_TOKEN='):
                BOT_TOKEN = line.strip().split('=', 1)[1]
                break

if not BOT_TOKEN:
    BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def generate_username():
    names = [
        'aayan', 'vihaan', 'rudra', 'atharv', 'shivansh', 'arnav', 'lakshya', 'vedant',
        'madhav', 'keshav', 'advait', 'nikhil', 'harsh', 'omkar', 'samar', 'pranav',
        'riya', 'kiara', 'isha', 'tanvi', 'meera', 'kavya', 'navya', 'prisha',
        'ethan', 'mason', 'logan', 'jack', 'owen', 'aiden', 'caleb', 'samuel',
        'daniel', 'matthew', 'joseph', 'david', 'andrew', 'julian'
    ]
    name = random.choice(names)
    name_part = name[:random.randint(6, 8)]
    numbers = str(random.randint(99, 999))
    letters = ''.join(random.choices(string.ascii_lowercase, k=2))
    return f"{name_part}{numbers}_{letters}"

def get_hotp_token(secret, intervals_no):
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return str(h).zfill(6)

def get_totp_token(secret):
    return get_hotp_token(secret, intervals_no=int(time.time())//30)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 GENERATE USERNAME", callback_data='generate')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *Instagram Username Generator*\n\n"
        "Tap button to generate unique username:\n\n"
        "Commands:\n"
        "/setpassword &lt;password&gt; - Set custom password\n"
        "Send your 2FA key to get OTP instantly",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    username = generate_username()
    password = context.user_data.get("password", "0plm0plm")
    message = f"""
✅ *Indo created succesfully*

Username = `{username}`

━━━━━━━━━━━━
Password = `{password}`
━━━━━━━━━━━━
"""
    keyboard = [
        [InlineKeyboardButton("🔄 GENERATE ANOTHER", callback_data='generate')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def quick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = generate_username()
    password = context.user_data.get("password", "0plm0plm")
    await update.message.reply_text(
        f"⚡ *Quick Generate*\n\n"
        f"Username: `{username}`\n"
        f"Password: `{password}`\n\n"
        f"📋 Tap & hold to copy",
        parse_mode='Markdown'
    )

async def set_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /setpassword &lt;your-password&gt;",
            parse_mode='Markdown'
        )
        return
    password = ' '.join(context.args)
    context.user_data["password"] = password
    await update.message.reply_text(
        f"✅ Password set successfully!\nNew password: `{password}`",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip().replace(" ", "").upper()
    try:
        otp = get_totp_token(message_text)
        await update.message.reply_text(
            f"🔐 Your OTP: `{otp}`\n\n"
            "(Valid for 30 seconds)",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(
            "Please send your 2FA secret key to get OTP, or use commands like /start, /gen, /setpassword."
        )

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found! Set it in Railway Variables.")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", quick_command))
    app.add_handler(CommandHandler("setpassword", set_password))
    app.add_handler(CallbackQueryHandler(generate_handler, pattern='^generate$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 BOT RUNNING ON RAILWAY...")
    app.run_polling()

if __name__ == '__main__':
    main()
