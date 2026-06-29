import os
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = os.getenv("BOT_TOKEN")

uyeler = {}
yapanlar = set()
gec_yapanlar = set()

def bagis_kontrol(text: str):
    text = text.lower().strip()
    pattern = r"^(bağış|bagis)\s*yap(ıldı|ildi)\.?\s*$"
    return bool(re.match(pattern, text))

def pazar_mi():
    return datetime.now().weekday() == 6


# kullanıcı kaydı
async def kayit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    user_id = str(user.id)
    username = user.username or "no_username"

    uyeler[user_id] = username

    text = update.message.text or ""

    if bagis_kontrol(text):
        if not pazar_mi():
            yapanlar.add(user_id)
        else:
            gec_yapanlar.add(user_id)


# manuel rapor
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await gonder_rapor(update.message.chat_id, context.bot)


# OTOMATİK RAPOR + RESET
async def gonder_rapor(chat_id, bot):
    tum = set(uyeler.keys())
    yapmayanlar = tum - yapanlar

    msg = "📊 HAFTALIK SON RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in yapanlar]) if yapanlar else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in yapmayanlar]) if yapmayanlar else "-"

    msg += "\n\n⚠ GEÇ YAPANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in gec_yapanlar]) if gec_yapanlar else "-"

    await bot.send_message(chat_id=chat_id, text=msg)

    # RESET
    yapanlar.clear()
    gec_yapanlar.clear()


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Bot aktif!")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kayit))


# 🔥 OTOMATİK Pazar 00:00
scheduler = AsyncIOScheduler()

def scheduled_job():
    # burası çalışınca rapor atılır ve resetlenir
    import asyncio
    asyncio.create_task(gonder_rapor(GROUP_CHAT_ID, app.bot))

scheduler.add_job(
    scheduled_job,
    "cron",
    day_of_week="sun",
    hour=0,
    minute=0
)

scheduler.start()

app.run_polling()
