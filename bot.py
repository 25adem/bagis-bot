import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

uyeler = set()
yapanlar = set()
gec_yapanlar = set()

def pazar_mi():
    return datetime.now().weekday() == 6

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif!")

# Grupta yazan herkesi otomatik ekler
async def kayit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        uyeler.add(str(update.message.from_user.id))

# Bağış kontrol
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    text = update.message.text.lower()

    uyeler.add(user_id)

    if "bağış" in text:
        if not pazar_mi():
            yapanlar.add(user_id)
        else:
            gec_yapanlar.add(user_id)

# Rapor
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    yapmayanlar = uyeler - yapanlar

    msg = "📊 HAFTALIK RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join(yapanlar) if yapanlar else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join(yapmayanlar) if yapmayanlar else "-"

    msg += "\n\n⚠ GEÇ YAPANLAR:\n"
    msg += "\n".join(gec_yapanlar) if gec_yapanlar else "-"

    await update.message.reply_text(msg)

    yapanlar.clear()
    gec_yapanlar.clear()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(MessageHandler(filters.ALL, kayit))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

app.run_polling()
