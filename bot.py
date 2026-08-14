import telebot
import os
import threading
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = "waiting_name"
    bot.reply_to(message, "Salom! 👋 Men botman. Ismingiz nima?")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text.lower()
    state = user_state.get(user_id)

    if state == "waiting_name":
        name = message.text
        user_state[user_id] = "chatting"
        bot.reply_to(message, f"Xursandman, {name}! Qalaysiz? 😊")
        return

    if "yaxshi" in text or "zoʻr" in text or "zo'r" in text:
        bot.reply_to(message, "Ajoyib! Sizga qanday yordam bera olaman? 🙂")
    elif "yomon" in text or "charchadim" in text:
        bot.reply_to(message, "Voy, kechirasiz eshitishga. Dam olganingiz maʼqul 💙")
    elif "salom" in text:
        bot.reply_to(message, "Salom yana! 👋")
    elif "raxmat" in text or "rahmat" in text:
        bot.reply_to(message, "Arzimaydi! Yana savolingiz bo'lsa yozing 😊")
    elif "yordam" in text or "help" in text:
        bot.reply_to(message, "Albatta yordam beraman. Nima haqida savolingiz bor?")
    else:
        bot.reply_to(message, "Tushunmadim, lekin tinglayapman... Yana bir bor ayting? 🤔")

# --- Render uchun soxta web-server ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Flask'ni alohida "thread"da ishga tushiramiz
threading.Thread(target=run_flask).start()

print("Bot ishga tushdi...")
bot.infinity_polling()
