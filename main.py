import os
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("API_TOKEN")
ADMIN_ID =7183586584 # BURAYA oz telegram ID-ni yazacaqsan
GROUP_ID =-1003831888867  # BURAYA qrup ID-ni yazacaqsan

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    expiry_date TEXT
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Terapiya", callback_data="terapiya")],
        [InlineKeyboardButton("Arıqlama", callback_data="ariqlama")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Qrupa xoş gəlmisiniz!\n\nAylıq ödəniş: 40 AZN / 30 gün\n\nZəhmət olmasa xidmət seçin:",
        reply_markup=reply_markup
    )

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    service = query.data
    user = query.from_user

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"{user.full_name} adlı istifadəçi {service} xidmətini seçdi.\nUsername: @{user.username}"
    )

    await query.edit_message_text(
        text="Zəhmət olmasa 40 AZN ödənişi kartla edin.\nÖdəniş linki tezliklə aktiv olacaq."
    )

async def check_expiry(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT user_id, expiry_date FROM users")
    users = cursor.fetchall()
    now = datetime.now()

    for user_id, expiry in users:
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
        if now > expiry_date:
            try:
                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
                cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
                conn.commit()
            except:
                pass

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(service_selected))

    app.job_queue.run_repeating(check_expiry, interval=86400, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()
