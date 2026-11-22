
import os
import random
import string
import logging
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# CONFIG
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_URL = os.getenv("ADMIN_URL", "https://t.me/your_admin")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =========================
# USERNAME GENERATOR
# =========================

def generate_username():
    names = [
        "aayan", "vihaan", "rudra", "atharv", "shivansh",
        "arnav", "lakshya", "vedant", "madhav", "keshav",
        "advait", "nikhil", "harsh", "omkar", "samar",
        "pranav", "riya", "kiara", "isha", "tanvi",
        "meera", "kavya", "navya", "prisha", "ethan",
        "mason", "logan", "jack", "owen", "aiden",
        "caleb", "samuel", "daniel", "matthew", "joseph",
        "david", "andrew", "julian"
    ]

    name = random.choice(names)
    name_part = name[:random.randint(3, len(name))]
    numbers = random.randint(99, 999)
    letters = "".join(random.choices(string.ascii_lowercase, k=2))

    return f"{name_part}{numbers}_{letters}"


# =========================
# DASHBOARD UI
# =========================

def dashboard_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎯 Generate Username",
                callback_data="username"
            )
        ],
        [
            InlineKeyboardButton(
                "🔐 2FA Demo Panel",
                callback_data="demo"
            )
        ],
        [
            InlineKeyboardButton(
                "📞 Contact Admin ↗",
                url=ADMIN_URL
            )
        ],
    ])


def demo_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Refresh Demo",
                callback_data="demo"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to Dashboard",
                callback_data="home"
            )
        ],
        [
            InlineKeyboardButton(
                "📞 Contact Admin ↗",
                url=ADMIN_URL
            )
        ],
    ])


def demo_panel_text():
    return (
        "🔐 *Legend* `Developer` · 2FA ✅\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔐 *Demo Code*\n\n"
        "`------`\n\n"
        "⌛ Demo mode — no real OTP generated\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "*Demo Key*\n"
        "`DEMO-KEY-NOT-A-SECRET`\n\n"
        "🧪 Sample interface only"
    )


# =========================
# /START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Username Generator Bot*\n\n"
        "Welcome! Choose an option below.\n\n"
        "🎯 Generate a username\n"
        "🔐 View demo dashboard\n"
        "⚙️ Set your custom password using /setpassword"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=dashboard_keyboard()
    )


# =========================
# USERNAME BUTTON
# =========================

async def username_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    username = generate_username()
    password = context.user_data.get("password", "0plm0plm")

    text = (
        "✅ *Username Generated*\n\n"
        f"Username: `{username}`\n\n"
        "━━━━━━━━━━━━━━\n"
        f"Password: `{password}`\n"
        "━━━━━━━━━━━━━━"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Generate Another",
                callback_data="username"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Dashboard",
                callback_data="home"
            )
        ]
    ])

    await query.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# =========================
# DEMO PANEL
# =========================

async def demo_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer("Demo panel")

    await query.message.reply_text(
        demo_panel_text(),
        parse_mode="Markdown",
        reply_markup=demo_keyboard()
    )


# =========================
# HOME CALLBACK
# =========================

async def home_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "🤖 *Username Generator Bot*\n\nSelect an option:",
        parse_mode="Markdown",
        reply_markup=dashboard_keyboard()
    )


# =========================
# /GEN
# =========================

async def quick_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    username = generate_username()
    password = context.user_data.get("password", "0plm0plm")

    await update.message.reply_text(
        "⚡ *Quick Generate*\n\n"
        f"Username: `{username}`\n"
        f"Password: `{password}`",
        parse_mode="Markdown"
    )


# =========================
# /SETPASSWORD
# =========================

async def set_password(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not context.args:
        await update.message.reply_text(
            "Usage: /setpassword your-password"
        )
        return

    password = " ".join(context.args)
    context.user_data["password"] = password

    await update.message.reply_text(
        "✅ Your custom password has been updated."
    )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(update, context):
    logger.error("Bot error: %s", context.error)


# =========================
# STARTUP: WEBHOOK CLEANUP
# =========================

async def post_init(application: Application):
    await application.bot.delete_webhook(
        drop_pending_updates=False
    )
    logger.info("Webhook cleared successfully.")


# =========================
# MAIN
# =========================

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing in Railway Variables!")
        return

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", quick_command))
    app.add_handler(CommandHandler("setpassword", set_password))

    app.add_handler(
        CallbackQueryHandler(
            username_callback,
            pattern="^username$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            demo_callback,
            pattern="^demo$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            home_callback,
            pattern="^home$"
        )
    )

    app.add_error_handler(error_handler)

    logger.info("Bot is starting...")

    app.run_polling(
        drop_pending_updates=False
    )


if __name__ == "__main__":
    main()
