import os
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# =========================
# DATABASE (RAM)
# =========================
uyeler = {}          # id -> name
bagis_sayaci = {}    # id -> count
haftalik = set()

# =========================
# BAĞIŞ ALGILAMA
# =========================
def bagis_kontrol(text):
    if not text:
        return False

    text = text.lower()

    return bool(re.search(r"(bağış|bagis).*(yap|yapt|gönd|att)", text))


# =========================
# ÜYE KAYDI (GARANTİ)
# =========================
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)

    # kayıt
    uyeler[uid] = user.username or user.first_name

    text = update.message.text or ""

    # bağış kontrol
    if bagis_kontrol(text):
        haftalik.add(uid)
        bagis_sayaci[uid] = bagis_sayaci.get(uid, 0) + 1


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot aktif! Panel hazır.")


# =========================
# ÜYELER PANELİ
# =========================
async def uyeler_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not uyeler:
        await update.message.reply_text("📭 Üye yok")
        return

    msg = "👥 ÜYE LİSTESİ\n\n"
    msg += "\n".join([f"{name} ({uid})" for uid, name in uyeler.items()])

    await update.message.reply_text(msg)


# =========================
# RAPOR
# =========================
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tum = set(uyeler.keys())
    yapmayan = tum - haftalik

    msg = "📊 HAFTALIK RAPOR\n\n"

    msg += "✔ YAPANLAR:\n"
    msg += "\n".join([uyeler[i] for i in haftalik]) if haftalik else "-"

    msg += "\n\n❌ YAPMAYANLAR:\n"
    msg += "\n".join([uyeler[i] for i in yapmayan]) if yapmayan else "-"

    await update.message.reply_text(msg)


# =========================
# İSTATİSTİK PANELİ
# =========================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = len(uyeler)
    active = len(haftalik)

    msg = f"""
📊 PANEL STATS

👥 Toplam Üye: {total}
💰 Bağış Yapan: {active}
📌 Mesaj Sayısı: {sum(bagis_sayaci.values())}
"""

    await update.message.reply_text(msg)


# =========================
# BOT SETUP
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(CommandHandler("uyeler", uyeler_cmd))
app.add_handler(CommandHandler("stats", stats))

# HER MESAJI YAKALA
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

app.run_polling()
