import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS donations (user_id TEXT, date TEXT)")
conn.commit()


# =========================
# BAĞIŞ KONTROL (SADECE NET)
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


def bagis_ekle(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO donations VALUES (?,?)", (uid, today))
    conn.commit()


# =========================
# MESAJ
# =========================
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    user_kaydet(uid, user.username or user.first_name)

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

    msg = "📊 RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([u[1] for u in users if u[0] in done]) or "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([u[1] for u in users if u[0] not in done]) or "-"

    await update.message.reply_text(msg)


# =========================
# Pazar 18:00 UYARI (DOĞRU YÖNTEM)
# =========================
async def pazar_uyari(context: ContextTypes.DEFAULT_TYPE):
    c.execute("SELECT * FROM users")
    users = c.fetchall()

    c.execute("SELECT user_id FROM donations")
    done = set([x[0] for x in c.fetchall()])

    missing = [u for u in users if u[0] not in done]

    msg = "⚠️ SON GÜN UYARISI ⚠️\n\n"

    for u in missing:
        msg += f"@{u[1]} bağış yapmayı unutma!\n"

    # grup id otomatik context.chat_id değil, sabit koyman gerekir
    await context.bot.send_message(chat_id=context.job.chat_id, text=msg)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif")


# =========================
# BOT SETUP
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))


# =========================
# JOB QUEUE (CRASHSIZ SİSTEM)
# =========================
job_queue = app.job_queue

job_queue.run_daily(
    pazar_uyari,
    time=datetime.strptime("18:00", "%H:%M").time(),
    days=(6,),  # Sunday
    chat_id=YOUR_GROUP_ID  # BURAYA GRUP ID YAZMALISIN
)

app.run_polling()
