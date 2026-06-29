import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

uyeler = {}
haftalik = set()
aylik = {}

# 🔥 BAĞIŞ KONTROL
def bagis_kontrol(text):
    if not text:
        return False

    text = text.lower()
    return "bağış" in text or "bagis" in text


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif")


# 🔥 TÜM MESAJLARI YAKALA (EN KRİTİK FIX)
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    # ✔ HERKESİ KAYDET (KESİN)
    uyeler[uid] = user.username or user.first_name

    text = update.message.text or ""

    if bagis_kontrol(text):
        haftalik.add(uid)
        aylik[uid] = aylik.get(uid, 0) + 1


# 📊 RAPOR
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tum = set(uyeler.keys())
    yapmayan = tum - haftalik

    msg = "📊 RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([uyeler[i] for i in haftalik]) if haftalik else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([uyeler[i] for i in yapmayan]) if yapmayan else "-"

    await update.message.reply_text(msg)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))

# 🔥 EN ÖNEMLİ SATIR (HER MESAJ)
app.add_handler(MessageHandler(filters.ALL, mesaj))

app.run_polling()
