import os
import re
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

# ADMIN LIST
ADMIN_IDS = {123456789}  # kendi telegram idn

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

# ================= DB =================
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
    return datetime.now().strftime("%Y-%W")

def month_id():
    return datetime.now().strftime("%Y-%m")

def is_admin(user_id: int):
    return user_id in ADMIN_IDS

# ================= USER =================
def add_user(uid, name):
    c.execute(
        "INSERT OR REPLACE INTO users VALUES (?,?,?)",
        (uid, name, datetime.now().isoformat())
    )
    conn.commit()

# ================= DONATION =================
def add_donation(uid):
    c.execute(
        "INSERT INTO donations (user_id, timestamp, week_id, month_id) VALUES (?,?,?,?)",
        (uid, datetime.now().isoformat(), week_id(), month_id())
    )
    conn.commit()

# ================= DETECTION =================
def detect_donation(text: str):
    if not text:
        return False

    t = text.lower()

    keywords = [
        "bağış yap",
        "bagis yap",
        "bağış yaptım",
        "bagis yaptim",
        "haftanın bağışı",
        "bagis yapildi",
        "bağış yapıldı",
    ]

    has_keyword = any(k in t for k in keywords)
    has_ss = bool(re.search(r"(ss|screenshot|ekran görüntüsü|kanıt)", t))

    return has_keyword or has_ss

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif 🚀")

# ADMIN ADD USER
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Yetkin yok")

    args = context.args
    if len(args) < 2:
        return await update.message.reply_text("Kullanım: /adduser id name")

    add_user(args[0], " ".join(args[1:]))
    await update.message.reply_text("Kullanıcı eklendi")

# LIST USERS
async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c.execute("SELECT * FROM users")
    users = c.fetchall()

    msg = "👥 ÜYELER\n\n"
    msg += "\n".join([f"{u[1]} ({u[0]})" for u in users]) or "-"
    await update.message.reply_text(msg)

# WEEKLY REPORT
async def haftalik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    w = week_id()

    c.execute("SELECT user_id FROM donations WHERE week_id=?", (w,))
    done = {i[0] for i in c.fetchall()}

    c.execute("SELECT * FROM users")
    users = c.fetchall()

    all_users = {u[0]: u[1] for u in users}

    missing = set(all_users.keys()) - done

    msg = f"📊 HAFTALIK RAPOR ({w})\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([all_users[i] for i in done]) or "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([all_users[i] for i in missing]) or "-"

    await update.message.reply_text(msg)

# MONTHLY
async def aylik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = month_id()

    c.execute("""
        SELECT users.name, COUNT(donations.id)
        FROM users
        LEFT JOIN donations
        ON users.id = donations.user_id AND donations.month_id=?
        GROUP BY users.id
    """, (m,))

    rows = c.fetchall()

    msg = "📊 AYLIK RAPOR\n\n"
    msg += "\n".join([f"{r[0]}: {r[1]}" for r in rows]) or "-"

    await update.message.reply_text(msg)

# ================= MESSAGE =================
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    add_user(uid, user.first_name or user.username)

    text = update.message.text or ""

    if detect_donation(text):
        add_donation(uid)

# ================= DAILY JOBS =================
async def sunday_warning(context: ContextTypes.DEFAULT_TYPE):
    c.execute("SELECT * FROM users")
    users = c.fetchall()

    msg = "⚠️ BUGÜN SON GÜN BAĞIŞ YAPMAYI UNUTMAYIN!\n\n"
    msg += "\n".join([u[1] for u in users])

    await context.bot.send_message(chat_id=ADMIN_IDS.pop(), text=msg)

async def final_report(context: ContextTypes.DEFAULT_TYPE):
    # simple weekly snapshot
    await context.bot.send_message(
        chat_id=list(ADMIN_IDS)[0],
        text="📊 Haftalık rapor zamanı (otomatik sistem çalıştı)"
    )

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("liste", liste))
app.add_handler(CommandHandler("haftalik", haftalik))
app.add_handler(CommandHandler("aylik", aylik))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

# JOBS
job = app.job_queue

# Sunday warning (18:00 örnek)
job.run_daily(sunday_warning, time=datetime.strptime("18:00", "%H:%M").time())

# Sunday final report (23:50)
job.run_daily(final_report, time=datetime.strptime("23:50", "%H:%M").time())

app.run_polling()
