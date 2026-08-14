import telebot
import os
import threading
from flask import Flask
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = -1003342853736  # Anonim savollar shu yerga keladi

bot = telebot.TeleBot(TOKEN)
user_state = {}

# ===== MATERIALLAR RO'YXATI =====
# Har bir fan uchun havola qo'shing (Google Drive link bo'lishi mumkin)
materials = {
    "Anatomiya": "https://drive.google.com/example-anatomiya",
    "Fiziologiya": "https://drive.google.com/example-fiziologiya",
    "Biokimyo": "https://drive.google.com/example-biokimyo",
}

# ===== /start =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "Salom! 👋 Men tibbiyot talabalari uchun botman.\n\n"
        "📚 /materiallar — konspekt va qo'llanmalar\n"
        "❓ /anon savolingiz — anonim savol yuborish\n"
        "ℹ️ /help — yordam"
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "Buyruqlar:\n"
        "/materiallar — fanlar bo'yicha materiallar\n"
        "/anon <savol> — anonim savol yuborish (masalan: /anon Imtihon qachon?)"
    )

# ===== MATERIALLAR =====
@bot.message_handler(commands=['materiallar'])
def show_materials(message):
    markup = types.InlineKeyboardMarkup()
    for subject in materials:
        markup.add(types.InlineKeyboardButton(subject, callback_data=f"mat_{subject}"))
    bot.send_message(message.chat.id, "📚 Qaysi fan kerak?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mat_"))
def send_material(call):
    subject = call.data.replace("mat_", "")
    link = materials.get(subject)
    if link:
        bot.send_message(call.message.chat.id, f"📄 {subject}:\n{link}")
    else:
        bot.send_message(call.message.chat.id, "Material topilmadi.")

# ===== ANONIM SAVOL =====
@bot.message_handler(commands=['anon'])
def anon_question(message):
    text = message.text.replace("/anon", "").strip()
    if not text:
        bot.reply_to(message, "Savolingizni yozing, masalan:\n/anon Imtihon qachon bo'ladi?")
        return
    bot.send_message(ADMIN_GROUP_ID, f"❓ Anonim savol:\n\n{text}")
    bot.reply_to(message, "✅ Savolingiz yuborildi (anonim).")

# ===== ODDIY SUHBAT =====
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.lower()
    if "salom" in text:
        bot.reply_to(message, "Salom! 👋")
    elif "raxmat" in text or "rahmat" in text:
        bot.reply_to(message, "Arzimaydi! 😊")
    else:
        bot.reply_to(message, "Buyruqlar uchun /help yozing.")

# ===== Render uchun soxta server =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

print("Bot ishga tushdi...")
bot.infinity_polling()
