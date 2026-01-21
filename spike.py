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

BOT_TOKEN = "7756376632:AAFdH6uGmSBOKWjFJrJEvO_LMC6b8k2sfos"
ADMINS = [1944789569]
AUTO_APPROVE_SECONDS = 60

FILES = {
    "normal": "normal_headshot.zip",
    "youtube": "youtube_pro_headshot.zip",
    "antenna": "antenna_headshot.zip",
    "brutal": "full_brutal_max.zip"
}

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, status TEXT)")
conn.commit()

def get_status(uid):
    cursor.execute("SELECT status FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    return r[0] if r else None

def set_status(uid, status):
    cursor.execute("REPLACE INTO users (user_id, status) VALUES (?,?)", (uid, status))
    conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([["📂 Menu", "💰 Pay"], ["📞 Contact Owner"]], resize_keyboard=True)
    await update.message.reply_text(\"👋 Welcome\\nMenu open karne ke liye 📂 Menu dabayein\", reply_markup=kb)

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if get_status(uid) == \"approved\":
        await update.message.reply_text(\"✅ Already approved\")
        return
    set_status(uid, \"pending\")
    await update.message.reply_text(\"💰 Payment ke baad screenshot bhejein\")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if get_status(uid) != \"pending\":
        return
    for admin in ADMINS:
        await update.message.forward(admin)
    await update.message.reply_text(\"⏳ Screenshot received, auto approval soon\")
    await asyncio.sleep(AUTO_APPROVE_SECONDS)
    set_status(uid, \"approved\")
    await context.bot.send_message(uid, \"🎉 Approved! Ab 📂 Menu open karo\")

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if get_status(update.effective_user.id) != \"approved\":
        await update.message.reply_text(\"❌ Aap approved nahi ho\")
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(\"🧠 Normal Headshot\", callback_data=\"normal\")],
        [InlineKeyboardButton(\"🎯 YouTube Pro Headshot\", callback_data=\"youtube\")],
        [InlineKeyboardButton(\"📡 Antenna Headshot\", callback_data=\"antenna\")],
        [InlineKeyboardButton(\"🔥 Full Brutal Max\", callback_data=\"brutal\")],
        [InlineKeyboardButton(\"📞 Contact Owner\", url=\"https://t.me/Yourspike\")]
    ])
    await update.message.reply_text(\"📂 Select option\", reply_markup=kb)

async def menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if get_status(uid) != \"approved\":
        return
    file = FILES.get(q.data)
    if not file:
        return
    try:
        await context.bot.send_document(uid, open(file, \"rb\"))
    except Exception:
        await context.bot.send_message(uid, \"❌ File missing\")

async def text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == \"📂 Menu\":
        await show_menu(update, context)
    elif t == \"💰 Pay\":
        await pay(update, context)
    elif t == \"📞 Contact Owner\":
        await update.message.reply_text(\"@Yourspike\")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(\"start\", start))
    app.add_handler(CommandHandler(\"menu\", show_menu))
    app.add_handler(CommandHandler(\"pay\", pay))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(menu_action))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_buttons))
    print(\"🤖 Bot running...\")
    app.run_polling()

if __name__ == \"__main__\":
    main()