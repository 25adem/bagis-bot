import os
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

uyeler = {}        
yapanlar = set()
gec_yapanlar = set()


# 🔥 BAĞIŞ ALGILAMA (ULTRA ESNEK)
def bagis_kontrol(text):
    if not text:
        return False

    text = text.lower()

    # tüm ihtimaller
    anahtarlar = [
        "bağış yapıldı",
        "bagis yapildi",
        "bağış yaptım",
        "bagis yaptim",
        "bağış yaptık",
        "bagis yaptik"
    ]

    return any(k in text for k in anahtarlar)


def pazar_mi():
    return datetime.now().weekday() == 6


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot aktif!")


# 🔥 ANA MESAJ HANDLER
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    print("MESAJ GELDİ")  # log için

    user = update.message.from_user
    uid = str(user.id)

    # kayıt
    uyeler[uid] = user.username or user.first_name

    text = update.message.text or ""

    # 🔥 BAĞIŞ TESPİT
    if bagis_kontrol(text):
        if not pazar_mi():
            yapanlar.add(uid)
            print(f"BAĞIŞ SAYILDI: {uid}")
        else:
            gec_yapanlar.add(uid)
            print(f"GEÇ BAĞIŞ: {uid}")


# 📊 RAPOR
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tum = set(uyeler.keys())
    yapmayanlar = tum - yapanlar

    msg = "📊 HAFTALIK BAĞIŞ RAPORU\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]}" for i in yapanlar]) if yapanlar else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]}" for i in yapmayanlar]) if yapmayanlar else "-"

    msg += "\n\n⚠ GEÇ YAPANLAR:\n"
    msg += "\n".join([f"@{uyeler[i]}" for i in gec_yapanlar]) if gec_yapanlar else "-"

    await update.message.reply_text(msg)


# 🔄 MANUEL RESET
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    yapanlar.clear()
    gec_yapanlar.clear()
    await update.message.reply_text("♻️ Liste sıfırlandı!")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(CommandHandler("reset", reset))

# 🔥 EN KRİTİK SATIR
app.add_handler(MessageHandler(filters.TEXT, mesaj))

print("BOT ÇALIŞIYOR...")
app.run_polling()
