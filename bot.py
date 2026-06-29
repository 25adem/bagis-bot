import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")

tum_uyeler = set()
yapanlar = set()
gec_yapanlar = set()

def pazar_mi():
    return datetime.now().weekday() == 6

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif!")

async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        tum_uyeler.add(context.args[0])
        await update.message.reply_text("Eklendi")

async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text
    if not text:
        return

    user_id = str(update.message.from_user.id)
    text = text.lower()

    if "bağış" in text:
        if not pazar_mi():
            yapanlar.add(user_id)
        else:
            gec_yapanlar.add(user_id)

async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    yapmayanlar = tum_uyeler - yapanlar

    msg = "HAFTALIK RAPOR\n\n"

    msg += "YAPANLAR:\n" + ("\n".join(yapanlar) if yapanlar else "-")
    msg += "\n\nYAPMAYANLAR:\n" + ("\n".join(yapmayanlar) if yapmayanlar else "-")
    msg += "\n\nGEÇ YAPANLAR:\n" + ("\n".join(gec_yapanlar) if gec_yapanlar else "-")

    await update.message.reply_text(msg)

    yapanlar.clear()
    gec_yapanlar.clear()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ekle", ekle))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

app.run_polling()
