import os
import re
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# TOKEN
# =========================
TOKEN = os.getenv("BOT_TOKEN")

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS donations (
    user_id TEXT,
    date TEXT
)
""")

conn.commit()


# =========================
# SAFE BAĞIŞ ALGILAMA
# =========================
def bagis_kontrol(text):
    if not text:
        return False

    text = text.lower().strip()

    return text in [
        "bağış yapıldı",
        "bagis yapildi",
        "bağış yaptım",
        "bagis yaptim",
        "bağış gönderildi",
        "bagis gonderildi"
    ]


# =========================
# USER KAYIT
# =========================
def user_kaydet(uid, name):
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?)", (uid, name))
    conn.commit()


# =========================
# BAĞIŞ KAYIT
# =========================
def bagis_ekle(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO donations VALUES (?,?)", (uid, today))
    conn.commit()


# =========================
# MESAJ HANDLER
# =========================
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)
    name = user.username or user.first_name

    user_kaydet(uid, name)

    text = update.message.text or ""

    if bagis_kontrol(text):
        bagis_ekle(uid)


# =========================
# RAPOR
# =========================
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c.execute("SELECT * FROM users")
    users = c.fetchall()

    c.execute("SELECT user_id FROM donations")
    done = set([x[0] for x in c.fetchall()])

    msg = "📊 HAFTALIK RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([u[1] for u in users if u[0] in done]) or "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([u[1] for u in users if u[0] not in done]) or "-"

    await update.message.reply_text(msg)


# =========================
# ÜYELER
# =========================
async def uyeler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c.execute("SELECT * FROM users")
    users = c.fetchall()

    msg = "👥 ÜYELER\n\n"
    msg += "\n".join([f"{u[1]} ({u[0]})" for u in users]) or "-"

    await update.message.reply_text(msg)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot aktif ve stabil çalışıyor")


# =========================
# BOT SETUP
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(CommandHandler("uyeler", uyeler))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

app.run_polling()
