import telebot
import os
import re
import threading
import requests
from flask import Flask
from telebot import types

# ================== SOZLAMALAR ==================
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = -1003342853736

bot = telebot.TeleBot(TOKEN)
user_state = {}
all_users = set()
watchlist = {}
anon_messages = {}

ANILIST_URL = "https://graphql.anilist.co"

def clean_html(text):
    if not text:
        return "Tavsif yo'q"
    text = re.sub('<br\s*/?>', '\n', text)
    text = re.sub('<[^<]+?>', '', text)
    return text

# ================== MENYU ==================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🎌 Anime qidirish"),
        types.KeyboardButton("📺 Mening ro'yxatim")
    )
    markup.add(
        types.KeyboardButton("🖼 Rasmlar"),
        types.KeyboardButton("❓ Anonim savol")
    )
    markup.add(types.KeyboardButton("ℹ️ Yordam"))
    return markup

def get_user_list(user_id):
    if user_id not in watchlist:
        watchlist[user_id] = {"korgan": [], "kormoqchi": []}
    return watchlist[user_id]

# ================== ASOSIY BUYRUQLAR ==================
@bot.message_handler(commands=['start'])
def start(message):
    all_users.add(message.chat.id)
    bot.send_message(
        message.chat.id,
        "🎌 Salom! Men sizning shaxsiy anime yordamchingizman.\n\n"
        "Anime qidiring, ko'rganlaringizni baholang, personajlar rasmini toping, "
        "yoki anonim savol bering 👇",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "📖 Buyruqlar:\n"
        "/anime <nom> — anime qidirish\n"
        "/royxat — mening watchlist'im\n"
        "/rasm <personaj ismi> — personaj rasmi\n"
        "/anon <savol> — anonim savol yuborish"
    )

# ================== ANIME QIDIRISH (AniList) ==================
def search_anime(query):
    gql = """
    query ($search: String) {
      Page(perPage: 3) {
        media(search: $search, type: ANIME) {
          title { romaji english }
          averageScore
          episodes
          description
        }
      }
    }
    """
    try:
        res = requests.post(
            ANILIST_URL,
            json={"query": gql, "variables": {"search": query}},
            timeout=10
        ).json()
        results = res.get("data", {}).get("Page", {}).get("media", [])
        if not results:
            return None, "❌ Anime topilmadi."
        return results, None
    except Exception:
        return None, "⚠️ Qidiruvda xatolik yuz berdi, birozdan keyin qayta urinib ko'ring."

@bot.message_handler(commands=['anime'])
def anime_cmd(message):
    query = message.text.replace("/anime", "").strip()
    if not query:
        bot.reply_to(message, "Anime nomini yozing, masalan:\n/anime Naruto")
        return
    do_anime_search(message, query)

def do_anime_search(message, query):
    results, error = search_anime(query)
    if error:
        bot.reply_to(message, error)
        return
    for anime in results:
        title = anime["title"].get("english") or anime["title"].get("romaji") or "Noma'lum"
        score = anime.get("averageScore", "N/A")
        episodes = anime.get("episodes", "N/A")
        synopsis = clean_html(anime.get("description"))[:300]
        text = f"🎌 <b>{title}</b>\n⭐ Reyting: {score}\n📺 Epizodlar: {episodes}\n\n{synopsis}..."
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Ko'rdim", callback_data=f"watched_{title}"),
            types.InlineKeyboardButton("📌 Ko'rmoqchiman", callback_data=f"want_{title}")
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

# ================== WATCHLIST TUGMALARI ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith("watched_"))
def mark_watched(call):
    title = call.data.replace("watched_", "")
    user_state[call.message.chat.id] = {"stage": "waiting_rating", "title": title}
    bot.send_message(call.message.chat.id, f"'{title}' ga nechchi ball berasiz? (1-10)")

@bot.callback_query_handler(func=lambda call: call.data.startswith("want_"))
def mark_want(call):
    title = call.data.replace("want_", "")
    user_list = get_user_list(call.message.chat.id)
    if title not in user_list["kormoqchi"]:
        user_list["kormoqchi"].append(title)
    bot.send_message(call.message.chat.id, f"📌 '{title}' ko'rmoqchilar ro'yxatiga qo'shildi!")

def show_watchlist(message):
    user_list = get_user_list(message.chat.id)
    text = "📺 <b>Sizning ro'yxatingiz</b>\n\n"
    text += "✅ <b>Ko'rganlarim:</b>\n"
    if user_list["korgan"]:
        for a in sorted(user_list["korgan"], key=lambda x: -x["reyting"]):
            text += f"  • {a['nom']} — ⭐{a['reyting']}/10\n"
    else:
        text += "  Hozircha yo'q\n"
    text += "\n📌 <b>Ko'rmoqchilarim:</b>\n"
    if user_list["kormoqchi"]:
        for a in user_list["kormoqchi"]:
            text += f"  • {a}\n"
    else:
        text += "  Hozircha yo'q\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['royxat'])
def royxat_cmd(message):
    show_watchlist(message)

# ================== RASMLAR (PERSONAJLAR, AniList) ==================
def search_character(query):
    gql = """
    query ($search: String) {
      Character(search: $search) {
        name { full }
        image { large }
        description
      }
    }
    """
    try:
        res = requests.post(
            ANILIST_URL,
            json={"query": gql, "variables": {"search": query}},
            timeout=10
        ).json()
        char = res.get("data", {}).get("Character")
        return char
    except Exception:
        return None

@bot.message_handler(commands=['rasm'])
def rasm_cmd(message):
    query = message.text.replace("/rasm", "").strip()
    if not query:
        bot.reply_to(message, "Personaj ismini yozing, masalan:\n/rasm Naruto")
        return
    do_character_search(message, query)

def do_character_search(message, query):
    char = search_character(query)
    if not char:
        bot.reply_to(message, "❌ Bunday personaj topilmadi.")
        return
    name = char.get("name", {}).get("full", "Noma'lum")
    image_url = char.get("image", {}).get("large")
    about = clean_html(char.get("description"))[:400]
    caption = f"🖼 <b>{name}</b>\n\n{about}..."
    if image_url:
        bot.send_photo(message.chat.id, image_url, caption=caption, parse_mode="HTML")
    else:
        bot.reply_to(message, f"Rasm topilmadi, lekin ma'lumot bor:\n{caption}", parse_mode="HTML")

# ================== ANONIM SAVOL (IKKI TOMONLAMA) ==================
@bot.message_handler(commands=['anon'])
def anon_question(message):
    text = message.text.replace("/anon", "").strip()
    if not text:
        bot.reply_to(message, "Savolingizni yozing, masalan:\n/anon Salom")
        return
    send_anon_to_group(message.chat.id, text)
    bot.reply_to(message, "✅ Savolingiz yuborildi (anonim). Javob kelsa, sizga xabar beraman.")

def send_anon_to_group(user_id, text):
    sent = bot.send_message(ADMIN_GROUP_ID, f"❓ Anonim savol:\n\n{text}")
    anon_messages[sent.message_id] = user_id

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_GROUP_ID and m.reply_to_message is not None)
def handle_admin_reply(message):
    replied_id = message.reply_to_message.message_id
    if replied_id in anon_messages:
        user_id = anon_messages[replied_id]
        try:
            bot.send_message(user_id, f"💬 Sizning savolingizga javob:\n\n{message.text}")
            bot.reply_to(message, "✅ Javob foydalanuvchiga anonim yuborildi.")
        except Exception:
            bot.reply_to(message, "⚠️ Javobni yuborib bo'lmadi.")

# ================== XABARLARNI QAYTA ISHLASH ==================
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    all_users.add(user_id)
    text = message.text

    if text == "🎌 Anime qidirish":
        user_state[user_id] = "waiting_anime"
        bot.send_message(user_id, "Anime nomini yozing:")
        return

    if text == "📺 Mening ro'yxatim":
        show_watchlist(message)
        return

    if text == "🖼 Rasmlar":
        user_state[user_id] = "waiting_character"
        bot.send_message(user_id, "Personaj ismini yozing (masalan: Naruto):")
        return

    if text == "❓ Anonim savol":
        user_state[user_id] = "waiting_anon"
        bot.send_message(user_id, "Savolingizni yozing, men uni anonim yuboraman:")
        return

    if text == "ℹ️ Yordam":
        help_cmd(message)
        return

    state = user_state.get(user_id)

    if state == "waiting_anime":
        do_anime_search(message, text)
        user_state[user_id] = None
        return

    if state == "waiting_character":
        do_character_search(message, text)
        user_state[user_id] = None
        return

    if state == "waiting_anon":
        send_anon_to_group(user_id, text)
        bot.reply_to(message, "✅ Savolingiz yuborildi (anonim). Javob kelsa, sizga xabar beraman.")
        user_state[user_id] = None
        return

    if isinstance(state, dict) and state.get("stage") == "waiting_rating":
        if text.isdigit() and 1 <= int(text) <= 10:
            title = state["title"]
            user_list = get_user_list(user_id)
            user_list["korgan"].append({"nom": title, "reyting": int(text)})
            bot.send_message(user_id, f"✅ '{title}' ⭐{text}/10 baho bilan saqlandi!")
            user_state[user_id] = None
        else:
            bot.send_message(user_id, "Iltimos, 1 dan 10 gacha raqam yozing.")
        return

    low = text.lower()
    if "salom" in low:
        bot.reply_to(message, "Salom! 👋")
    elif "raxmat" in low or "rahmat" in low:
        bot.reply_to(message, "Arzimaydi! 😊")
    else:
        bot.reply_to(message, "Buyruqlar uchun pastdagi tugmalardan foydalaning.")

# ================== RENDER UCHUN SERVER ==================
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
