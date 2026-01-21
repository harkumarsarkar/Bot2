import sqlite3 import asyncio import time from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

================= CONFIG =================

BOT_TOKEN = "7756376632:AAFdH6uGmSBOKWjFJrJEvO_LMC6b8k2sfos" ADMINS = [1944789569] AUTO_APPROVE_SECONDS = 60

================= DATABASE =================

conn = sqlite3.connect("users.db", check_same_thread=False) cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, status TEXT, expiry INTEGER)") cursor.execute("CREATE TABLE IF NOT EXISTS menus (key TEXT PRIMARY KEY, title TEXT, file TEXT, price INTEGER, expiry INTEGER)") conn.commit()

================= HELPERS =================

def is_admin(uid): return uid in ADMINS

def get_status(uid): if is_admin(uid): return "approved" cursor.execute("SELECT status FROM users WHERE user_id=?", (uid,)) r = cursor.fetchone() return r[0] if r else None

def set_status(uid, status, expiry=None): if is_admin(uid): return cursor.execute("REPLACE INTO users (user_id, status, expiry) VALUES (?,?,?)", (uid, status, expiry)) conn.commit()

================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): kb = ReplyKeyboardMarkup([["📂 Menu", "💰 Pay"], ["📞 Contact Owner"]], resize_keyboard=True) await update.message.reply_text("👋 Welcome\n📂 Menu dabao", reply_markup=kb)

================= PAY =================

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE): uid = update.effective_user.id if get_status(uid) == "approved": await update.message.reply_text("✅ Aap already approved ho") return set_status(uid, "pending") await update.message.reply_text("💰 Payment ke baad screenshot bhejo")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): uid = update.effective_user.id if get_status(uid) != "pending": return for admin in ADMINS: await update.message.forward(admin) await asyncio.sleep(AUTO_APPROVE_SECONDS) set_status(uid, "approved", int(time.time()) + 86400) await context.bot.send_message(uid, "🎉 Approved! /menu")

================= MENU SHOW =================

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE): if get_status(update.effective_user.id) != "approved": await update.message.reply_text("❌ Access denied") return

cursor.execute("SELECT key,title,price FROM menus")
rows = cursor.fetchall()
buttons = []
i = 1
for k, t, p in rows:
    buttons.append([InlineKeyboardButton(f"{i}️⃣ {t} (₹{p})", callback_data=k)])
    i += 1
buttons.append([InlineKeyboardButton("📞 Contact Owner", url="https://t.me/Yourspike")])

await update.message.reply_text("📂 Floating Menu", reply_markup=InlineKeyboardMarkup(buttons))

================= MENU CLICK =================

async def menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE): q = update.callback_query await q.answer() uid = q.from_user.id

cursor.execute("SELECT file,expiry FROM menus WHERE key=?", (q.data,))
row = cursor.fetchone()
if not row:
    return
file, expiry_hours = row
try:
    await context.bot.send_document(uid, open(file, "rb"))
except:
    await context.bot.send_message(uid, "❌ File missing")

================= ADMIN MENU COMMANDS =================

async def add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE): if not is_admin(update.effective_user.id): return # /addmenu key title price expiryHours file if len(context.args) < 5: await update.message.reply_text("Usage: /addmenu key title price expiryHours file") return key, title, price, expiry, file = context.args cursor.execute("REPLACE INTO menus VALUES (?,?,?,?,?)", (key, title, file, int(price), int(expiry))) conn.commit() await update.message.reply_text("✅ Menu added/updated")

async def change_price(update: Update, context: ContextTypes.DEFAULT_TYPE): if not is_admin(update.effective_user.id): return key, price = context.args cursor.execute("UPDATE menus SET price=? WHERE key=?", (int(price), key)) conn.commit() await update.message.reply_text("✅ Price updated")

async def change_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE): if not is_admin(update.effective_user.id): return key, expiry = context.args cursor.execute("UPDATE menus SET expiry=? WHERE key=?", (int(expiry), key)) conn.commit() await update.message.reply_text("✅ Expiry updated")

================= TEXT BUTTONS =================

async def text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE): t = update.message.text if t == "📂 Menu": await show_menu(update, context) elif t == "💰 Pay": await pay(update, context) elif t == "📞 Contact Owner": await update.message.reply_text("@Yourspike")

================= MAIN =================

def main(): app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", show_menu))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(CommandHandler("addmenu", add_menu))
app.add_handler(CommandHandler("price", change_price))
app.add_handler(CommandHandler("expiry", change_expiry))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(CallbackQueryHandler(menu_action))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_buttons))

print("🤖 Bot running...")
app.run_polling()

if name == "main": main()