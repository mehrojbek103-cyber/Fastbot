import telebot
import os
import threading
from flask import Flask
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = -1003342853736

bot = telebot.TeleBot(TOKEN)
user_state = {}

# ===== MATERIALLAR RO'YXATI =====
materials = {
    "Anatomiya": "https://drive.google.com/example-anatomiya",
    "Fiziologiya": "https://drive.google.com/example-fiziologiya",
    "Biokimyo": "https://drive.google.com/example-biokimyo",
}

# ===== DOIMIY MENYU (pastdagi tugmalar) =====
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📚 Materiallar"),
        types.KeyboardButton("❓ Anonim savol")
    )
    markup.add(types.KeyboardButton("ℹ️ Yordam"))
    return markup

# ===== /start =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Salom! 👋 Men tibbiyot talabalari uchun botman.\n\n"
        "Pastdagi tugmalardan foydalaning 👇",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "Buyruqlar:\n"
        "/materiallar — fanlar bo'yicha materiallar\n"
        "/anon <savol> — anonim savol yuborish"
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

# ===== ANONIM SAVOL (buyruq orqali) =====
@bot.message_handler(commands=['anon'])
def anon_question(message):
    text = message.text.replace("/anon", "").strip()
    if not text:
        bot.reply_to(message, "Savolingizni yozing, masalan:\n/anon Imtihon qachon bo'ladi?")
        return
    bot.send_message(ADMIN_GROUP_ID, f"❓ Anonim savol:\n\n{text}")
    bot.reply_to(message, "✅ Savolingiz yuborildi (anonim).")

# ===== ASOSIY MENYU TUGMALARI VA SUHBAT =====
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text

    # Tugma: Materiallar
    if text == "📚 Materiallar":
        show_materials(message)
        return

    # Tugma: Anonim savol
    if text == "❓ Anonim savol":
        user_state[user_id] = "waiting_anon"
        bot.send_message(user_id, "Savolingizni yozing, men uni anonim yuboraman:")
        return

    # Tugma: Yordam
    if text == "ℹ️ Yordam":
        help_cmd(message)
        return

    # Agar foydalanuvchi anonim savol yozish holatida bo'lsa
    if user_state.get(user_id) == "waiting_anon":
        bot.send_message(ADMIN_GROUP_ID, f"❓ Anonim savol:\n\n{text}")
        bot.reply_to(message, "✅ Savolingiz yuborildi (anonim).")
        user_state[user_id] = None
        return

    # Oddiy suhbat
    low = text.lower()
    if "salom" in low:
        bot.reply_to(message, "Salom! 👋")
    elif "raxmat" in low or "rahmat" in low:
        bot.reply_to(message, "Arzimaydi! 😊")
    else:
        bot.reply_to(message, "Buyruqlar uchun pastdagi tugmalardan yoki /help dan foydalaning.")

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
