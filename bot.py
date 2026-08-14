import telebot
import os
import threading
import time
import schedule
from flask import Flask
from telebot import types

# ================== SOZLAMALAR ==================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = -1003342853736

bot = telebot.TeleBot(TOKEN)
user_state = {}
reminders = {}
all_users = set()

materials = {
    "Anatomiya": "https://drive.google.com/example-anatomiya",
    "Fiziologiya": "https://drive.google.com/example-fiziologiya",
    "Biokimyo": "https://drive.google.com/example-biokimyo",
}

books = {
    "Gray's Anatomy": "https://drive.google.com/example-book1",
    "Robbins Patologiya": "https://drive.google.com/example-book2",
    "Harrison Ichki kasalliklar": "https://drive.google.com/example-book3",
}

# Tibbiy atamalar lug'ati — shu formatda to'ldirasiz/ko'paytirasiz
dictionary = {
    "tahikardiya": "Yurak urish tezligining me'yordan (100 zarba/daq dan) oshib ketishi.",
    "bradikardiya": "Yurak urish tezligining me'yordan (60 zarba/daq dan) pastroq bo'lishi.",
    "gipertoniya": "Qon bosimining me'yordan yuqori bo'lishi (140/90 mmHg dan yuqori).",
    "gipotoniya": "Qon bosimining me'yordan past bo'lishi (90/60 mmHg dan past).",
    "anemiya": "Qonda gemoglobin yoki eritrotsitlar sonining kamayishi (kamqonlik).",
    "yallig'lanish": "To'qimaning zararlanishga javoban paydo bo'ladigan himoya reaktsiyasi.",
    "nekroz": "To'qima yoki hujayralarning o'lishi.",
    "gipoksiya": "To'qimalarda kislorod yetishmovchiligi.",
}

# ================== MENYU ==================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📚 Materiallar"),
        types.KeyboardButton("📖 Kitoblar")
    )
    markup.add(
        types.KeyboardButton("🔍 Lug'at"),
        types.KeyboardButton("❓ Anonim savol")
    )
    markup.add(
        types.KeyboardButton("⏰ Eslatma qo'shish"),
        types.KeyboardButton("📋 Eslatmalarim")
    )
    markup.add(
        types.KeyboardButton("👥 Foydalanuvchilar"),
        types.KeyboardButton("ℹ️ Yordam")
    )
    return markup

# ================== ASOSIY BUYRUQLAR ==================
@bot.message_handler(commands=['start'])
def start(message):
    all_users.add(message.chat.id)
    bot.send_message(
        message.chat.id,
        "Salom! 👋 Men tibbiyot talabalari uchun botman.\n\n"
        "Pastdagi tugmalardan foydalaning 👇",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "📖 Buyruqlar:\n"
        "/materiallar — fanlar bo'yicha materiallar\n"
        "/kitoblar — kitoblar ro'yxati\n"
        "/lugat <atama> — tibbiy atama ma'nosini bilish\n"
        "/anon <savol> — anonim savol yuborish\n"
        "⏰ Eslatma qo'shish — har kuni belgilangan vaqtda eslatma"
    )

# ================== STATISTIKA ==================
@bot.message_handler(commands=['stats'])
def stats(message):
    bot.reply_to(message, f"👥 Jami foydalanuvchilar: {len(all_users)}")

@bot.message_handler(commands=['foydalanuvchilar'])
def public_stats(message):
    bot.reply_to(message, f"👥 Botdan {len(all_users)} kishi foydalanmoqda!")

# ================== MATERIALLAR ==================
@bot.message_handler(commands=['materiallar'])
def show_materials(message):
    all_users.add(message.chat.id)
    markup = types.InlineKeyboardMarkup()
    for subject in materials:
        markup.add(types.InlineKeyboardButton(subject, callback_data=f"mat_{subject}"))
    bot.send_message(message.chat.id, "📚 Qaysi fan kerak?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mat_"))
def send_material(call):
    subject = call.data.replace("mat_", "")
    link = materials.get(subject)
    bot.send_message(call.message.chat.id, f"📄 {subject}:\n{link}" if link else "Material topilmadi.")

# ================== KITOBLAR ==================
@bot.message_handler(commands=['kitoblar'])
def show_books(message):
    all_users.add(message.chat.id)
    markup = types.InlineKeyboardMarkup()
    for book in books:
        markup.add(types.InlineKeyboardButton(book, callback_data=f"book_{book}"))
    bot.send_message(message.chat.id, "📖 Qaysi kitob kerak?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("book_"))
def send_book(call):
    book_name = call.data.replace("book_", "")
    link = books.get(book_name)
    bot.send_message(call.message.chat.id, f"📘 {book_name}:\n{link}" if link else "Kitob topilmadi.")

# ================== LUG'AT ==================
def search_dictionary(query):
    query = query.lower().strip()
    if query in dictionary:
        return f"📖 {query.capitalize()}:\n{dictionary[query]}"
    matches = [k for k in dictionary if query in k]
    if matches:
        text = "🔍 Topilgan atamalar:\n\n"
        for m in matches:
            text += f"📖 {m.capitalize()}:\n{dictionary[m]}\n\n"
        return text.strip()
    return "❌ Bu atama lug'atda topilmadi. Boshqa so'z bilan urinib ko'ring."

@bot.message_handler(commands=['lugat'])
def lugat_cmd(message):
    all_users.add(message.chat.id)
    query = message.text.replace("/lugat", "").strip()
    if not query:
        bot.reply_to(message, "Atama yozing, masalan:\n/lugat tahikardiya")
        return
    bot.reply_to(message, search_dictionary(query))

# ================== ANONIM SAVOL ==================
@bot.message_handler(commands=['anon'])
def anon_question(message):
    all_users.add(message.chat.id)
    text = message.text.replace("/anon", "").strip()
    if not text:
        bot.reply_to(message, "Savolingizni yozing, masalan:\n/anon Imtihon qachon bo'ladi?")
        return
    bot.send_message(ADMIN_GROUP_ID, f"❓ Anonim savol:\n\n{text}")
    bot.reply_to(message, "✅ Savolingiz yuborildi (anonim).")

# ================== ESLATMALAR ==================
def show_reminders(message):
    user_id = message.chat.id
    user_reminders = reminders.get(user_id, [])
    if not user_reminders:
        bot.send_message(user_id, "Sizda hozircha eslatma yo'q.")
        return
    text = "📋 Sizning eslatmalaringiz:\n\n"
    for i, r in enumerate(user_reminders, 1):
        text += f"{i}. ⏰ {r['time']} — {r['text']}\n"
    bot.send_message(user_id, text)

# ================== XABARLARNI QAYTA ISHLASH ==================
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    all_users.add(user_id)
    text = message.text

    if text == "📚 Materiallar":
        show_materials(message)
        return

    if text == "📖 Kitoblar":
        show_books(message)
        return

    if text == "🔍 Lug'at":
        user_state[user_id] = "waiting_dict"
        bot.send_message(user_id, "Tibbiy atamani yozing (masalan: tahikardiya):")
        return

    if text == "❓ Anonim savol":
        user_state[user_id] = "waiting_anon"
        bot.send_message(user_id, "Savolingizni yozing, men uni anonim yuboraman:")
        return

    if text == "⏰ Eslatma qo'shish":
        user_state[user_id] = "waiting_time"
        bot.send_message(user_id, "Eslatma vaqtini yozing (masalan: 14:30):")
        return

    if text == "📋 Eslatmalarim":
        show_reminders(message)
        return

    if text == "👥 Foydalanuvchilar":
        bot.reply_to(message, f"👥 Botdan {len(all_users)} kishi foydalanmoqda!")
        return

    if text == "ℹ️ Yordam":
        help_cmd(message)
        return

    state = user_state.get(user_id)

    if state == "waiting_dict":
        bot.reply_to(message, search_dictionary(text))
        user_state[user_id] = None
        return

    if state == "waiting_anon":
        bot.send_message(ADMIN_GROUP_ID, f"❓ Anonim savol:\n\n{text}")
        bot.reply_to(message, "✅ Savolingiz yuborildi (anonim).")
        user_state[user_id] = None
        return

    if state == "waiting_time":
        if len(text) == 5 and text[2] == ":":
            user_state[user_id] = {"stage": "waiting_text", "time": text}
            bot.send_message(user_id, "Endi eslatma matnini yozing (masalan: Anatomiya darsiga tayyorgarlik):")
        else:
            bot.send_message(user_id, "Noto'g'ri format. Masalan: 14:30 shaklida yozing.")
        return

    if isinstance(state, dict) and state.get("stage") == "waiting_text":
        reminder_time = state["time"]
        reminders.setdefault(user_id, []).append({"time": reminder_time, "text": text})
        bot.send_message(user_id, f"✅ Eslatma saqlandi!\nHar kuni soat {reminder_time} da eslataman: {text}")
        user_state[user_id] = None
        return

    low = text.lower()
    if "salom" in low:
        bot.reply_to(message, "Salom! 👋")
    elif "raxmat" in low or "rahmat" in low:
        bot.reply_to(message, "Arzimaydi! 😊")
    else:
        bot.reply_to(message, "Buyruqlar uchun pastdagi tugmalardan yoki /help dan foydalaning.")

# ================== ESLATMALARNI TEKSHIRISH ==================
def check_reminders():
    now = time.strftime("%H:%M")
    for chat_id, user_reminders in reminders.items():
        for r in user_reminders:
            if r["time"] == now:
                bot.send_message(chat_id, f"⏰ Eslatma: {r['text']}")

def run_scheduler():
    schedule.every().minute.do(check_reminders)
    while True:
        schedule.run_pending()
        time.sleep(20)

# ================== RENDER UCHUN SERVER ==================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ================== ISHGA TUSHIRISH ==================
threading.Thread(target=run_flask).start()
threading.Thread(target=run_scheduler).start()

print("Bot ishga tushdi...")
bot.infinity_polling()
