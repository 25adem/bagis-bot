import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

uyeler = {}          # {id: username}
yapanlar = set()
gec_yapanlar = set()

def pazar_mi():
    return datetime.now().weekday() == 6

def format_user(user_id):
    username = uyeler.get(user_id)
    if username:
        return f"@{username} ({user_id})"
    return f"{user_id}"

async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    user_id = str(user.id)
    username = user.username

    uyeler[user_id] = username  # kaydet

    text = update.message.text.lower() if update.message.text else ""

    if "bağış" in text:
        if not pazar_mi():
            yapanlar.add(user_id)
        else:
            gec_yapanlar.add(user_id)

async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    yapmayanlar = set(uyeler.keys()) - yapanlar

    msg = "📊 HAFTALIK RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([format_user(x) for x in yapanlar]) if yapanlar else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([format_user(x) for x in yapmayanlar]) if yapmayanlar else "-"

    msg += "\n\n⚠ GEÇ YAPANLAR:\n"
    msg += "\n".join([format_user(x) for x in gec_yapanlar]) if gec_yapanlar else "-"

    await update.message.reply_text(msg)

    yapanlar.clear()
    gec_yapanlar.clear()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))
app.add_handler(CommandHandler("rapor", rapor))

app.run_polling()
