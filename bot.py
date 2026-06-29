import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

uyeler = {}
yapanlar = set()
gec_yapanlar = set()

def bagis_kontrol(text):
    return text and text.lower().strip() in ["bağış yapıldı", "bagis yapildi"]

def pazar_mi():
    return datetime.now().weekday() == 6


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif!")


async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    uyeler[uid] = user.username or "no_username"

    text = update.message.text

    if bagis_kontrol(text):
        if not pazar_mi():
            yapanlar.add(uid)
        else:
            gec_yapanlar.add(uid)


async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tum = set(uyeler.keys())
    yapmayanlar = tum - yapanlar

    msg = "📊 HAFTALIK RAPOR\n\n"

    msg += "✔ Yapanlar:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in yapanlar]) if yapanlar else "-"

    msg += "\n\n❌ Yapmayanlar:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in yapmayanlar]) if yapmayanlar else "-"

    msg += "\n\n⚠ Geç yapanlar:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in gec_yapanlar]) if gec_yapanlar else "-"

    await update.message.reply_text(msg)

    yapanlar.clear()
    gec_yapanlar.clear()


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

app.run_polling()
