import os
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# =====================
# VERİLER
# =====================
uyeler = {}          # user_id -> username
haftalik_yapanlar = set()
gec_yapanlar = set()
aylik_sayac = {}     # user_id -> count

# =====================
# BAĞIŞ KONTROL
# =====================
def bagis_kontrol(text):
    if not text:
        return False

    text = text.lower()

    return bool(re.search(r"(bağış|bagis).*(yapıldı|yapildi|yaptım|yaptim)", text))


# =====================
# KULLANICI KAYIT
# =====================
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    # kayıt
    uyeler[uid] = user.username or user.first_name

    text = update.message.text or ""

    # BAĞIŞ ALGILAMA
    if bagis_kontrol(text):
        haftalik_yapanlar.add(uid)
        aylik_sayac[uid] = aylik_sayac.get(uid, 0) + 1
    else:
        # hiç bağış yoksa sonradan "yapmadı" sayılır
        pass


# =====================
# RAPOR (GENEL)
# =====================
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tum = set(uyeler.keys())
    yapmayanlar = tum - haftalik_yapanlar

    msg = "📊 HAFTALIK RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([f"{uyeler[i]}" for i in haftalik_yapanlar]) if haftalik_yapanlar else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([f"{uyeler[i]}" for i in yapmayanlar]) if yapmayanlar else "-"

    await update.message.reply_text(msg)


# =====================
# HAFTALIK RESET
# =====================
async def haftalik_reset(context: ContextTypes.DEFAULT_TYPE):
    haftalik_yapanlar.clear()
    gec_yapanlar.clear()


# =====================
# AYLIK RAPOR
# =====================
async def aylik_rapor(context: ContextTypes.DEFAULT_TYPE):
    if not aylik_sayac:
        return

    msg = "📊 AYLIK BAĞIŞ RAPORU\n\n"

    for uid, count in aylik_sayac.items():
        msg += f"{uyeler.get(uid,'?')} : {count}\n"

    await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

    aylik_sayac.clear()


# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif!")


# =====================
# BOT
# =====================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

# =====================
# SCHEDULER
# =====================
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Pazar 00:00 reset
scheduler.add_job(lambda: None, "cron", day_of_week="sun", hour=0, minute=0)

scheduler.start()

app.run_polling()
