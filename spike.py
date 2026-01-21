import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ========= CONFIG =========
BOT_TOKEN = "7756376632:AAFdH6uGmSBOKWjFJrJEvO_LMC6b8k2sfos"
ADMINS = [1944789569]
AUTO_APPROVE_SECONDS = 60

FILES = {
    "normal": "normal_headshot.zip",
    "youtube": "youtube_pro_headshot.zip",
    "antenna": "antenna_headshot.zip",
    "brutal": "full_brutal_max.zip"
}

# ========= DATABASE =========
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, status TEXT)"
)
conn.commit()

# ========= HELPERS =========
def get_status(user_id):
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None

def set_status(user_id, status):
    cursor.execute(
        "REPLACE INTO users (user_id, status) VALUES (?, ?)",
        (user_id, status)
    )
    conn.commit()

# ========= COMMANDS =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [["📂 Menu", "💰 Pay"], ["📞 Contact Owner"]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "👋 Welcome!\nMenu open karne ke liye 📂 Menu dabayein",
        reply_markup=keyboard
    )

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if get_status(user_id) == "approved":
        await update.message.reply_text("✅ Aap already approved ho")
        return
    set_status(user_id, "pending")
    await update.message.reply_text(
        "💰 Payment ke baad screenshot bhejiye"
    )

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if get_status(user_id) != "pending":
        return

    for admin in ADMINS:
        await update.message.forward(admin)

    await update.message.reply_text(
        "⏳ Screenshot mil gaya, thodi der me approval milega"
    )

    await asyncio.sleep(AUTO_APPROVE_SECONDS)
    set_status(user_id, "approved")
    await context.bot.send_message(
        user_id,
        "🎉 Approved!\nAb 📂 Menu open karo"
    )

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if get_status(update.effective_user.id) != "approved":
        await update.message.reply_text("❌ Aap approved nahi ho")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Normal Headshot", callback_data="normal")],
        [InlineKeyboardButton("🎯 YouTube Pro Headshot", callback_data="youtube")],
        [InlineKeyboardButton("📡 Antenna Headshot", callback_data="antenna")],
        [InlineKeyboardButton("🔥 Full Brutal Max", callback_data="brutal")],
        [InlineKeyboardButton("📞 Contact Owner", url="https://t.me/Yourspike")]
    ])

    await update.message.reply_text(
        "📂 Option select karo",
        reply_markup=keyboard
    )

async def menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if get_status(user_id) != "approved":
        await query.edit_message_text("❌ Access denied")
        return

    file_path = FILES.get(query.data)
    if not file_path:
        return

    try:
        await context.bot.send_document(
            chat_id=user_id,
            document=open(file_path, "rb")
        )
    except Exception:
        await context.bot.send_message(
            user_id,
            "❌ File server par nahi hai"
        )

async def text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📂 Menu":
        await show_menu(update, context)
    elif text == "💰 Pay":
        await pay(update, context)
    elif text == "📞 Contact Owner":
        await update.message.reply_text("@Yourspike")

# ========= MAIN =========
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(menu_action))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_buttons))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()