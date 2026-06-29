import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# DATABASE
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS donations (user_id TEXT, date TEXT)")
conn.commit()


# USER KAYIT
def user_kaydet(uid, name):
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?)", (uid, name))
    conn.commit()


# BAĞIŞ KAYIT (BASİT)
def bagis_ekle(uid):
    c.execute("INSERT INTO donations VALUES (?,?)", (uid, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()


# MESAJ
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)
    name = user.username or user.first_name

    user_kaydet(uid, name)

    text = (update.message.text or "").lower()

    # EN BASİT KONTROL
    if "bağış" in text and ("yapıldı" in text or "yaptım" in text):
        bagis_ekle(uid)


# RAPOR
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


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

app.run_polling()
