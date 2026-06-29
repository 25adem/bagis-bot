import os
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

uyeler = {}        # user_id -> username
yapanlar = set()
gec_yapanlar = set()

# 🔥 BAĞIŞ KONTROL (PRO MAX)
def bagis_kontrol(text):
    if not text:
        return False

    text = text.lower().strip()

    # bağış / bagis + yapıldı / yapildi (esnek)
    return re.search(r"(bağış|bagis).*(yapıldı|yapildi)", text) is not None


def pazar_mi():
    return datetime.now().weekday() == 6


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Bot aktif!")


# kullanıcı kaydı + bağış kontrol
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    uyeler[uid] = user.username or "no_username"

    text = update.message.text

    # 🔥 BAĞIŞ SAYMA
    if bagis_kontrol(text):
        if not pazar_mi():
            yapanlar.add(uid)
        else:
            gec_yapanlar.add(uid)


# 📊 RAPOR
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tum = set(uyeler.keys())
    yapmayanlar = tum - yapanlar

    msg = "📊 HAFTALIK BAĞIŞ RAPORU\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in yapanlar]) if yapanlar else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in yapmayanlar]) if yapmayanlar else "-"

    msg += "\n\n⚠ GEÇ YAPANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]} ({i})" for i in gec_yapanlar]) if gec_yapanlar else "-"

    await update.message.reply_text(msg)

    # 🔄 RESET
    yapanlar.clear()
    gec_yapanlar.clear()


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

app.run_polling()
