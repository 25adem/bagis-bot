import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

uyeler = {}
haftalik = set()
aylik = {}

def bagis_kontrol(text):
    if not text:
        return False
    text = text.lower()
    return re.search(r"(bağış|bagis).*(yapıldı|yapildi|yaptım|yaptim)", text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif")


async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    uyeler[uid] = user.username or user.first_name

    text = update.message.text or ""

    if bagis_kontrol(text):
        haftalik.add(uid)
        aylik[uid] = aylik.get(uid, 0) + 1


async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tum = set(uyeler.keys())
    yapmayan = tum - haftalik

    msg = "📊 RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([uyeler[i] for i in haftalik]) if haftalik else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([uyeler[i] for i in yapmayan]) if yapmayan else "-"

    await update.message.reply_text(msg)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    haftalik.clear()
    await update.message.reply_text("Reset atıldı")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

app.run_polling()
