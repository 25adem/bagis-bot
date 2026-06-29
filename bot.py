import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

members = set()
done = set()
late = set()

def is_sunday():
    return datetime.now().weekday() == 6

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is active!")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        members.add(context.args[0])
        await update.message.reply_text("Added")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    text = update.message.text.lower()

    if "donation" in text or "bağış" in text:
        if not is_sunday():
            done.add(user_id)
        else:
            late.add(user_id)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    missing = members - done

    msg = "WEEKLY REPORT\n\n"

    msg += "DONE:\n"
    msg += "\n".join(done) if done else "-"

    msg += "\n\nMISSING:\n"
    msg += "\n".join(missing) if missing else "-"

    msg += "\n\nLATE:\n"
    msg += "\n".join(late) if late else "-"

    await update.message.reply_text(msg)

    done.clear()
    late.clear()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

# IMPORTANT FIX FOR RAILWAY
if __name__ == "__main__":
    app.run_polling(drop_pending_updates=True)
