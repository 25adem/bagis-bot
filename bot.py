import os
import re
import sqlite3
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, JobQueue
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
TZ = pytz.timezone("Europe/Istanbul")

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, name TEXT, added_date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS donations (
    user_id TEXT, week TEXT, month TEXT, date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS weekly_snapshots (
    week TEXT PRIMARY KEY, snapshot TEXT, created_at TEXT
)""")

conn.commit()

# =========================
# YARDIMCI
# =========================
def get_week_key():
    return datetime.now(TZ).strftime("%Y-W%W")

def get_month_key():
    return datetime.now(TZ).strftime("%Y-%m")

def is_admin(uid):
    return uid in ADMIN_IDS

def get_all_users():
    c.execute("SELECT id, name FROM users ORDER BY name")
    return c.fetchall()

def get_week_donors(week=None):
    if not week:
        week = get_week_key()
    c.execute("SELECT DISTINCT user_id FROM donations WHERE week=?", (week,))
    return set(row[0] for row in c.fetchall())

def get_month_donors(month=None):
    if not month:
        month = get_month_key()
    c.execute("SELECT DISTINCT user_id FROM donations WHERE month=?", (month,))
    return set(row[0] for row in c.fetchall())

# =========================
# BAGIS ALGILAMA
# =========================
def normalize(text):
    replacements = {
        'I': 'i', 'İ': 'i', 'Ğ': 'g', 'Ü': 'u',
        'Ş': 's', 'Ö': 'o', 'Ç': 'c',
        'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', 'ı': 'i'
    }
    result = ""
    for ch in text:
        result += replacements.get(ch, ch.lower())
    return result

BAGIS_KEYWORDS = [
    "bagis yapildi", "bagis yapilmistir", "haftanin bagisi",
    "bagisimi yaptim", "bagisimi gonderdim", "bagis attim",
    "bagis yaptim", "haftalik bagis", "bagisi yaptim",
    "bagisi attim", "bagisi gonderdim", "bagisimi attim",
    "haftanin bagisini yaptim", "haftanin bagisini attim",
]

def is_donation_message(text, has_photo):
    if not text and not has_photo:
        return False
    if text:
        t = normalize(text)
        for kw in BAGIS_KEYWORDS:
            if kw in t:
                return True
    return False

# =========================
# KAYIT
# =========================
def user_kaydet(uid, name):
    now = datetime.now(TZ).strftime("%Y-%m-%d")
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (uid, name, now))
    conn.commit()

def bagis_ekle(uid):
    week = get_week_key()
    month = get_month_key()
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    c.execute("SELECT 1 FROM donations WHERE user_id=? AND week=?", (uid, week))
    if not c.fetchone():
        c.execute("INSERT INTO donations VALUES (?,?,?,?)", (uid, week, month, now))
        conn.commit()
        return True
    return False

# =========================
# MESAJ HANDLER
# =========================
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    uid = str(user.id)
    name = user.username or user.first_name
    text = update.message.text or update.message.caption or ""
    has_photo = bool(update.message.photo)

    # Kayıtlı değilse otomatik ekle
    c.execute("SELECT 1 FROM users WHERE id=?", (uid,))
    if not c.fetchone():
        user_kaydet(uid, name)

    if is_donation_message(text, has_photo):
        yeni = bagis_ekle(uid)
        if yeni:
            await update.message.reply_text(f"✅ @{name} bu haftaki bağışın kaydedildi!")

# =========================
# KOMUTLAR
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bağış Takip Botu Aktif*\n\n"
        "/hafta — Bu haftanın durumu\n"
        "/ay — Bu ayın özeti\n"
        "/rapor — Detaylı rapor\n"
        "/uyeler — Tüm üyeler\n"
        "/panel — Admin paneli\n"
        "/uyeekle [id] [isim]\n"
        "/uyesil [id]\n"
        "/bagisekle [id]\n"
        "/bagissil [id]\n"
        "/sifirla",
        parse_mode="Markdown"
    )

async def hafta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    donors = get_week_donors()
    yapanlar = [u for u in users if u[0] in donors]
    yapmayanlar = [u for u in users if u[0] not in donors]

    msg = f"📊 *{get_week_key()} — HAFTALIK DURUM*\n\n"
    msg += f"✅ *YAPANLAR ({len(yapanlar)}/{len(users)}):*\n"
    msg += "\n".join([f"  • @{u[1]}" for u in yapanlar]) if yapanlar else "  —"
    msg += f"\n\n❌ *YAPMAYANLAR ({len(yapmayanlar)}):*\n"
    msg += "\n".join([f"  • @{u[1]}" for u in yapmayanlar]) if yapmayanlar else "  —"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def ay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    month = get_month_key()
    c.execute("SELECT user_id, COUNT(*) FROM donations WHERE month=? GROUP BY user_id", (month,))
    rows = {r[0]: r[1] for r in c.fetchall()}

    msg = f"📅 *{month} — AYLIK BAĞIŞ*\n\n"
    for u in users:
        sayi = rows.get(u[0], 0)
        emoji = "✅" if sayi > 0 else "❌"
        msg += f"{emoji} {u[1]}: {sayi} bağış\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    donors = get_week_donors()
    yapanlar = [u for u in users if u[0] in donors]
    yapmayanlar = [u for u in users if u[0] not in donors]
    yuzde = int(len(yapanlar) / len(users) * 100) if users else 0

    msg = f"📋 *DETAYLI HAFTALIK RAPOR*\n"
    msg += f"📅 Hafta: {get_week_key()} | 📈 %{yuzde}\n\n"
    msg += f"✅ *YAPANLAR:*\n"
    msg += "\n".join([f"  {i+1}. @{u[1]}" for i, u in enumerate(yapanlar)]) if yapanlar else "  —"
    msg += f"\n\n❌ *YAPMAYANLAR:*\n"
    msg += "\n".join([f"  {i+1}. @{u[1]}" for i, u in enumerate(yapmayanlar)]) if yapmayanlar else "  —"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def uyeler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    if not users:
        await update.message.reply_text("Henüz kayıtlı üye yok.")
        return
    msg = f"👥 *KAYITLI ÜYELER ({len(users)} kişi)*\n\n"
    msg += "\n".join([f"  {i+1}. {u[1]} (`{u[0]}`)" for i, u in enumerate(users)])
    await update.message.reply_text(msg, parse_mode="Markdown")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("⛔ Yetkisiz.")
        return

    users = get_all_users()
    week_donors = get_week_donors()
    month_donors = get_month_donors()
    yapanlar = [u for u in users if u[0] in week_donors]
    yapmayanlar = [u for u in users if u[0] not in week_donors]

    msg = f"🛠 *ADMİN PANELİ*\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"👥 Toplam: {len(users)} | ✅ Yapan: {len(yapanlar)} | ❌ Yapmayan: {len(yapmayanlar)}\n"
    msg += f"📅 Hafta: {get_week_key()} | 📆 Ay: {get_month_key()}\n"
    msg += f"📊 Bu ay tekil bağışçı: {len(month_donors)}\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"✅ *YAPANLAR:*\n"
    msg += "\n".join([f"  • @{u[1]} (`{u[0]}`)" for u in yapanlar]) if yapanlar else "  —"
    msg += f"\n\n❌ *YAPMAYANLAR:*\n"
    msg += "\n".join([f"  • @{u[1]} (`{u[0]}`)" for u in yapmayanlar]) if yapmayanlar else "  —"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def uyeekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("⛔ Yetkisiz.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Kullanım: /uyeekle [id] [isim]")
        return
    uid, name = args[0], " ".join(args[1:])
    user_kaydet(uid, name)
    await update.message.reply_text(f"✅ {name} (`{uid}`) eklendi.", parse_mode="Markdown")

async def uyesil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("⛔ Yetkisiz.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Kullanım: /uyesil [id]")
        return
    uid = args[0]
    c.execute("SELECT name FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    if not row:
        await update.message.reply_text("❌ Bulunamadı.")
        return
    c.execute("DELETE FROM users WHERE id=?", (uid,))
    c.execute("DELETE FROM donations WHERE user_id=?", (uid,))
    conn.commit()
    await update.message.reply_text(f"🗑 {row[0]} silindi.")

async def bagisekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("⛔ Yetkisiz.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Kullanım: /bagisekle [id]")
        return
    uid = args[0]
    c.execute("SELECT name FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    if not row:
        await update.message.reply_text("❌ Kullanıcı bulunamadı.")
        return
    yeni = bagis_ekle(uid)
    if yeni:
        await update.message.reply_text(f"✅ {row[0]} için bağış eklendi.")
    else:
        await update.message.reply_text(f"ℹ️ {row[0]} zaten bu hafta yapmış.")

async def bagissil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("⛔ Yetkisiz.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Kullanım: /bagissil [id]")
        return
    uid = args[0]
    c.execute("DELETE FROM donations WHERE user_id=? AND week=?", (uid, get_week_key()))
    conn.commit()
    await update.message.reply_text(f"🗑 `{uid}` için bu haftaki bağış silindi.", parse_mode="Markdown")

async def sifirla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("⛔ Yetkisiz.")
        return
    await haftalik_rapor_gonder(context)
    await update.message.reply_text("✅ Rapor gönderildi ve hafta sıfırlandı.")

# =========================
# PAZAR 18:00 — ETİKETLİ UYARI
# =========================
async def pazar_hatirlatma(context: ContextTypes.DEFAULT_TYPE):
    if not GROUP_ID:
        return
    users = get_all_users()
    donors = get_week_donors()
    yapmayanlar = [u for u in users if u[0] not in donors]

    if not yapmayanlar:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text="🎉 Bu hafta tüm üyeler bağışını tamamladı!"
        )
        return

    etiketler = " ".join([f"@{u[1]}" for u in yapmayanlar])
    msg = (
        f"⏰ *HATIRLATMA — Bugün Son Gün!*\n\n"
        f"Bağışını henüz yapmayan üyeler:\n{etiketler}\n\n"
        f"🙏 Lütfen bağışınızı yapmayı unutmayınız!"
    )
    await context.bot.send_message(chat_id=GROUP_ID, text=msg, parse_mode="Markdown")

# =========================
# PAZAR 23:50 — RAPOR ADMİNE
# =========================
async def haftalik_rapor_gonder(context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    week = get_week_key()
    donors = get_week_donors(week)
    yapanlar = [u for u in users if u[0] in donors]
    yapmayanlar = [u for u in users if u[0] not in donors]
    yuzde = int(len(yapanlar) / len(users) * 100) if users else 0

    snapshot = (
        f"📋 *{week} — HAFTA SONU RAPORU*\n"
        f"📈 Tamamlama: {len(yapanlar)}/{len(users)} (%{yuzde})\n\n"
        f"✅ Bağış Yapanlar ({len(yapanlar)}):\n"
        + ("\n".join([f"  • @{u[1]}" for u in yapanlar]) or "  —")
        + f"\n\n❌ Bağış Yapmayanlar ({len(yapmayanlar)}):\n"
        + ("\n".join([f"  • @{u[1]}" for u in yapmayanlar]) or "  —")
    )

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT OR REPLACE INTO weekly_snapshots VALUES (?,?,?)", (week, snapshot, now))
    conn.commit()

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text="🔔 *Pazar 23:50 — Haftalık Son Rapor:*\n\n" + snapshot,
                parse_mode="Markdown"
            )
        except Exception:
            pass

# =========================
# PAZARTESİ 00:00 — SIFIRLA
# =========================
async def haftalik_sifirla(context: ContextTypes.DEFAULT_TYPE):
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text="🔄 *Yeni hafta başladı!* Bağış takibi sıfırlandı.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

# =========================
# ZAMANLAYICILAR
# =========================
def schedule_jobs(app):
    jq: JobQueue = app.job_queue

    # Pazar 18:00 — yapmayanlara etiketli uyarı
    jq.run_daily(
        pazar_hatirlatma,
        time=datetime.strptime("18:00", "%H:%M").replace(tzinfo=TZ).timetz(),
        days=(6,)
    )

    # Pazar 23:50 — raporu adminlere gönder
    jq.run_daily(
        haftalik_rapor_gonder,
        time=datetime.strptime("23:50", "%H:%M").replace(tzinfo=TZ).timetz(),
        days=(6,)
    )

    # Pazartesi 00:00 — sıfırla
    jq.run_daily(
        haftalik_sifirla,
        time=datetime.strptime("00:00", "%H:%M").replace(tzinfo=TZ).timetz(),
        days=(0,)
    )

# =========================
# ANA UYGULAMA
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hafta", hafta))
app.add_handler(CommandHandler("ay", ay))
app.add_handler(CommandHandler("rapor", rapor))
app.add_handler(CommandHandler("uyeler", uyeler))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(CommandHandler("uyeekle", uyeekle))
app.add_handler(CommandHandler("uyesil", uyesil))
app.add_handler(CommandHandler("bagisekle", bagisekle))
app.add_handler(CommandHandler("bagissil", bagissil))
app.add_handler(CommandHandler("sifirla", sifirla))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))
app.add_handler(MessageHandler(filters.PHOTO, mesaj))

schedule_jobs(app)

print("✅ Bot başlatıldı.")
app.run_polling()
    
