import os
import re
import sqlite3
from datetime import datetime, time
from pytz import timezone

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN missing in environment variables")

ADMIN_IDS = {123456789}  # kendi telegram idn

TR = timezone("Europe/Istanbul")

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT,
    created_at TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    timestamp TEXT,
    week_id TEXT,
    month_id TEXT
)
""")

conn.commit()

# ================= HELPERS =================
def week_id():
    return datetime.now(TR).strftime("%Y-%W")

def month_id():
    return datetime.now(TR).strftime("%Y-%m")

def add_user(uid, name):
    c.execute(
        "INSERT OR REPLACE INTO users VALUES (?,?,?)",
        (uid, name, datetime.now(TR).isoformat())
    )
    conn.commit()

def add_donation(uid):
    c.execute(
        "INSERT INTO donations (user_id, timestamp, week_id, month_id) VALUES (?,?,?,?)",
        (uid, datetime.now(TR).isoformat(), week_id(), month_id())
    )
    conn.commit()

def detect_donation(text: str):
    if not text:
        return False

    t = text.lower()

    keywords = [
        "bağış",
        "bagis",
        "bağış yapıldı",
        "bagis yapildi",
        "bağış yaptım",
        "bagis yaptim",
        "haftanın bağışı",
    ]

    has_keyword = any(k in t for k in keywords)
    has_ss = bool(re.search(r"(ss|screenshot|ekran görüntü|kanıt)", t))

    return has_keyword or has_ss

def get_all_users():
    c.execute("SELECT * FROM users")
    return c.fetchall()

def get_done_users_week():
    c.execute("SELECT user_id FROM donations WHERE week_id=?", (week_id(),))
    return {i[0] for i in c.fetchall()}

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif 🚀")

async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    msg = "👥 ÜYELER\n\n"
    msg += "\n".join([f"{u[1]} ({u[0]})" for u in users]) or "-"
    await update.message.reply_text(msg)

async def haftalik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    done = get_done_users_week()

    all_users = {u[0]: u[1] for u in users}
    missing = set(all_users.keys()) - done

    msg = f"📊 HAFTALIK RAPOR ({week_id()})\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([all_users[i] for i in done]) or "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([all_users[i] for i in missing]) or "-"

    await update.message.reply_text(msg)

# ================= MESSAGE HANDLER =================
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    add_user(uid, user.first_name or user.username or "user")

    text = update.message.text or ""

    if detect_donation(text):
        add_donation(uid)

# ================= PAST SUNDAY WARNING =================
async def sunday_warning(context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()

    if not users:
        return

    mentions = "\n".join([f"👤 {u[1]}" for u in users])

    msg = (
        "⚠️ BUGÜN BAĞIŞ İÇİN SON GÜN!\n\n"
        f"{mentions}\n\n"
        "Bağış yapmayı unutmayın."
    )

    # tüm adminlere gönder
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(chat_id=admin_id, text=msg)

# ================= FINAL REPORT =================
async def sunday_final_report(context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    done = get_done_users_week()

    all_users = {u[0]: u[1] for u in users}
    missing = set(all_users.keys()) - done

    msg = "📊 HAFTALIK FİNAL RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([all_users[i] for i in done]) or "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([all_users[i] for i in missing]) or "-"

    for admin_id in ADMIN_IDS:
        await context.bot.send_message(chat_id=admin_id, text=msg)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    job = app.job_queue

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("haftalik", haftalik))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

    # 🇹🇷 Sunday 18:00 warning
    job.run_daily(
        sunday_warning,
        time=time(hour=18, minute=0, tzinfo=TR),
        days=(6,)  # Sunday = 6
    )

    # 🇹🇷 Sunday 23:50 final report
    job.run_daily(
        sunday_final_report,
        time=time(hour=23, minute=50, tzinfo=TR),
        days=(6,)
    )

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
