import sqlite3
import asyncio
import time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
BOT_TOKEN = "7756376632:AAFdH6uGmSBOKWjFJrJEvO_LMC6b8k2sfos"
ADMINS = [1944789569]

# ================= DATABASE =================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    status TEXT,
    expiry INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS menus (
    key TEXT PRIMARY KEY,
    title TEXT,
    file TEXT,
    price INTEGER,
    expiry INTEGER
)
""")

conn.commit()

# ================= HELPERS =================
def is_admin(uid):
    return uid in ADMINS

def is_approved(uid):
    if is_admin(uid):
        return True
    cursor.execute("SELECT expiry FROM users WHERE user_id=?", (uid,))
    row = cursor.fetchone()
    if not row:
        return False
    if row[0] == 0:
        return True
    return row[0] > int(time.time())

def approve_user(uid, hours):
    if hours == 0:
        expiry = 0
    else:
        expiry = int(time.time()) + hours * 3600
    cursor.execute(
        "REPLACE INTO users (user_id, status, expiry) VALUES (?,?,?)",
        (uid, "approved", expiry)
    )
    conn.commit()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [["📂 Menu", "💰 Pay"], ["📞 Contact Owner"]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "👋 Welcome\n📂 Menu dabao",
        reply_markup=kb
    )

# ================= PAY =================
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_approved(update.effective_user.id):
        await update.message.reply_text("✅ Aap already approved ho")
        return
    await update.message.reply_text(
        "💰 Payment karke UTR bhejo (secure system)"
    )

# ================= MENU SHOW =================
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_approved(update.effective_user.id):
        await update.message.reply_text("❌ Payment required")
        return

    cursor.execute("SELECT key,title,price FROM menus")
    rows = cursor.fetchall()

    buttons = []
    i = 1
    for k, t, p in rows:
        buttons.append([
            InlineKeyboardButton(f"{i}️⃣ {t} (₹{p})", callback_data=k)
        ])
        i += 1

    buttons.append([
        InlineKeyboardButton("📞 Contact Owner", url="https://t.me/Yourspike")
    ])

    await update.message.reply_text(
        "📂 Floating Menu",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= MENU CLICK =================
async def menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not is_approved(q.from_user.id):
        await q.edit_message_text("❌ Access denied")
        return

    cursor.execute(
        "SELECT file FROM menus WHERE key=?",
        (q.data,)
    )
    row = cursor.fetchone()
    if not row:
        return

    try:
        await context.bot.send_document(
            q.from_user.id,
            open(row[0], "rb")
        )
    except:
        await context.bot.send_message(
            q.from_user.id,
            "❌ File missing"
        )

# ================= ADMIN COMMANDS =================
async def add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    # /addmenu key title price expiryHours file
    if len(context.args) < 5:
        await update.message.reply_text(
            "Usage: /addmenu key title price expiryHours file"
        )
        return
    key, title, price, expiry, file = context.args
    cursor.execute(
        "REPLACE INTO menus VALUES (?,?,?,?,?)",
        (key, title, file, int(price), int(expiry))
    )
    conn.commit()
    await update.message.reply_text("✅ Menu added/updated")

# ================= TEXT BUTTONS =================
async def text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📂 Menu":
        await show_menu(update, context)
    elif update.message.text == "💰 Pay":
        await pay(update, context)
    elif update.message.text == "📞 Contact Owner":
        await update.message.reply_text("@Yourspike")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("addmenu", add_menu))
    app.add_handler(CallbackQueryHandler(menu_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_buttons))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()