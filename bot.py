import telebot
from telebot import types
from flask import Flask
import threading
import os
import sqlite3
import datetime
import time

# ==========================================
# НАСТРОЙКИ
# ==========================================
BOT_TOKEN = "9104960855:AAHa8wTH_Gq58lO-jUCTn4cnDIOR7lWZjMA"
MANAGER_USERNAME = "pagerNft"     # Менеджер
OWNER_USERNAME = "Slawua_shop"    # Владелец
REVIEWS_CHANNEL = "otzivi_slawua" # Канал с отзывами
SUB_CHANNEL = "@Novosti_SlawuaShop" # Канал для подписки

# ID ВЛАДЕЛЬЦА И МЕНЕДЖЕРА
OWNER_ID = 8739809998
MANAGER_ID = 7704432355

bot = telebot.TeleBot(BOT_TOKEN)
DB_NAME = "shop.db"

# ==========================================
# БАЗА ДАННЫХ
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            reg_date TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            discount INTEGER,
            uses_left INTEGER
        )
    """)
    
    # Добавляем тестовый промокод, если база пустая
    cur.execute("SELECT COUNT(*) FROM promocodes")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO promocodes (code, discount, uses_left) VALUES (?, ?, ?)", ("SLAWUA", 10, 5))
        
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cur.fetchone():
        reg_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cur.execute("INSERT INTO users (user_id, username, reg_date) VALUES (?, ?, ?)",
                    (user_id, username, reg_date))
        conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = [row[0] for row in cur.fetchall()]
    conn.close()
    return users

# ==========================================
# ПРОВЕРКА ПОДПИСКИ
# ==========================================
def check_sub(user_id):
    if user_id in [OWNER_ID, MANAGER_ID]:
        return True
    try:
        member = bot.get_chat_member(SUB_CHANNEL, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return False

def sub_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{SUB_CHANNEL.replace('@', '')}"))
    kb.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sub"))
    return kb

# ==========================================
# КЛАВИАТУРЫ
# ==========================================
def get_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🛒 Купить аккаунты"),
        types.KeyboardButton("💰 Скупка NFT"),
        types.KeyboardButton("📜 Как купить?"),
        types.KeyboardButton("⭐ Отзывы"),
        types.KeyboardButton("ℹ️ О магазине"),
        types.KeyboardButton("💬 Связаться с продавцом"),
        types.KeyboardButton("🎁 Промокод")
    )
    return kb

def get_shop_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🌍 Обычные аккаунты (по странам)", callback_data="show_regular"),
        types.InlineKeyboardButton("✨ Необычные аккаунты (поштучно)", callback_data="show_unusual"),
        types.InlineKeyboardButton("🔄 Обновить наличие", callback_data="refresh_stock")
    )
    return kb

# ==========================================
# СПИСКИ АККАУНТОВ
# ==========================================
ACCOUNTS_TEXT = """
🇺🇸 США +1 авторег - 21 шт. - 0.50$ ≈ 40.81₽
🇬🇧 Великобритания +44 авторег - 6 шт. - 1.00$ ≈ 81.61₽
🇧🇷 Бразилия +55 - 42 шт. - 1.00$ ≈ 81.61₽
🇰🇿 Казахстан +77 отлега до года - 9 шт. - 1.70$ ≈ 138.74₽
🇮🇩 Индонезия +62 отлега до года - 12 шт. - 0.80$ ≈ 65.29₽
🇲🇲 Мьянма +95 отлега до года - 22 шт. - 0.40$ ≈ 32.64₽
🇧🇩 Бангладеш +880 отлега до года - 15 шт. - 0.80$ ≈ 65.29₽
🇯🇵 Япония +81 авторег - 2 шт. - 2.50$ ≈ 204.03₽
🇵🇱 Польша +48 отлега до года - 2 шт. - 1.50$ ≈ 122.42₽
🇨🇳 Китай +86 авторег - 2 шт. - 1.20$ ≈ 97.93₽
🇹🇷 Турция +90 авторег - 7 шт. - 1.20$ ≈ 97.93₽
🇧🇪 Бельгия +32 авторег - 7 шт. - 3.00$ ≈ 244.83₽
🇹🇲 Туркменистан +993 авторег 6+мес - 16 шт. - 1.30$ ≈ 106.09₽
🇮🇳 Индия +91 авторег 1-5 лет - 146 шт. - 0.80$ ≈ 65.29₽
🇺🇦 Украина +380 авторег - 4 шт. - 3.00$ ≈ 244.83₽
🇺🇿 Узбекистан +998, 1-2 года - 3 шт. - 2.00$ ≈ 163.22₽
🇹🇯 Таджикистан +992 от 3 мес до года - 16 шт. - 1.10$ ≈ 89.77₽
"""

FAKE_IDS = """
#710 🇷🇺 Россия +7 2019 — 7.50$ ≈ 612.08₽
#711 🇷🇺 Россия +7 2019 — 7.50$ ≈ 612.08₽
#712 🇷🇺 Россия +7 2019 — 7.50$ ≈ 612.08₽
#716 🇷🇺 Россия +7 2021 — 6.40$ ≈ 522.30₽
#717 🇷🇺 Россия +7 2021 — 6.40$ ≈ 522.30₽
#718 🇷🇺 Россия +7 2021 — 6.40$ ≈ 522.30₽
#719 🇷🇺 Россия +7 2021 — 6.40$ ≈ 522.30₽
#720 🇷🇺 Россия +7 2021 — 6.40$ ≈ 522.30₽
#638 🇺🇸 США +1 2019 — 3.20$ ≈ 261.15₽
#642 🇺🇸 США +1 2019 — 3.20$ ≈ 261.15₽
#643 🇺🇸 США +1 2019 — 3.20$ ≈ 261.15₽
#644 🇺🇸 США +1 2019 — 3.20$ ≈ 261.15₽
#645 🇺🇸 США +1 2019 — 3.20$ ≈ 261.15₽
#646 🇺🇸 США +1 2019 — 3.20$ ≈ 261.15₽
"""

# ==========================================
# ХЕНДЛЕРЫ
# ==========================================
@bot.message_handler(commands=['start'])
def start_handler(message):
    add_user(message.from_user.id, message.from_user.username)

    if not check_sub(message.from_user.id):
        text = (
            "<b>👋 Добро пожаловать в Slawua SHOP!</b>\n\n"
            "Для продолжения работы с ботом, пожалуйста, подпишись на наш канал с новостями.\n\n"
            "👇 Подпишись и нажми «Я подписался»."
        )
        bot.send_message(message.chat.id, text, reply_markup=sub_keyboard(), parse_mode="HTML")
        return

    text = (
        "<b>Slawua SHOP</b> 🛍\n\n"
        "Добро пожаловать в наш магазин Telegram-аккаунтов и NFT!\n\n"
        "Мы предлагаем качественные аккаунты из разных стран, а также скупаем и продаем NFT.\n\n"
        "Выбери нужный раздел в меню ниже, чтобы начать."
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Подписка подтверждена!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        text = (
            "<b>Slawua SHOP</b> 🛍\n\n"
            "Добро пожаловать! Теперь тебе доступны все разделы магазина.\n\n"
            "Выбери нужный раздел в меню ниже:"
        )
        bot.send_message(call.message.chat.id, text, reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        bot.answer_callback_query(call.id, "❌ Ты еще не подписался на канал!", show_alert=True)

# ==========================================
# КОМАНДЫ ДЛЯ АДМИНОВ
# ==========================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id not in [OWNER_ID, MANAGER_ID]:
        return
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM promocodes")
    total_promos = cur.fetchone()[0]
    conn.close()
    
    text = (
        "<b>📊 Админ-панель Slawua SHOP</b>\n\n"
        f"👤 Всего пользователей: <b>{total_users}</b>\n"
        f"🎁 Активных промокодов: <b>{total_promos}</b>\n\n"
        "Команды:\n"
        "/addpromo [код] [скидка%] [кол-во] — создать промокод\n"
        "/promos — список промокодов\n"
        "/rassylka — сделать рассылку"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['addpromo'])
def add_promo(message):
    if message.from_user.id not in [OWNER_ID, MANAGER_ID]:
        return
    try:
        args = message.text.split()
        if len(args) < 4:
            bot.reply_to(message, "❌ Формат: /addpromo [код] [скидка] [кол-во активаций]\nПример: /addpromo SALE10 10 5")
            return
        code = args[1].upper()
        discount = int(args[2])
        uses = int(args[3])
        
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO promocodes (code, discount, uses_left) VALUES (?, ?, ?)", (code, discount, uses))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Промокод <b>{code}</b> создан!\nСкидка: {discount}%\nАктиваций: {uses}", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['promos'])
def list_promos(message):
    if message.from_user.id not in [OWNER_ID, MANAGER_ID]:
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT code, discount, uses_left FROM promocodes")
    promos = cur.fetchall()
    conn.close()
    
    if not promos:
        bot.reply_to(message, "🎁 Промокодов пока нет.")
        return
        
    text = "<b>🎁 Список промокодов:</b>\n\n"
    for p in promos:
        text += f"<code>{p[0]}</code> — скидка {p[1]}% (осталось: {p[2]})\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['rassylka'])
def broadcast(message):
    if message.from_user.id not in [OWNER_ID, MANAGER_ID]:
        return
    
    msg = bot.send_message(message.chat.id, "✍️ Отправь мне текст для рассылки (можно с картинкой):")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    users = get_all_users()
    bot.send_message(message.chat.id, f"🚀 Начинаю рассылку для {len(users)} пользователей...")
    
    success = 0
    fail = 0
    
    for user_id in users:
        try:
            bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
            time.sleep(0.05)
        except Exception:
            fail += 1
    
    bot.send_message(message.chat.id, f"✅ Рассылка окончена!\nУспешно: {success}\nОшибок: {fail}")

# ==========================================
# ПРОМОКОДЫ ДЛЯ КЛИЕНТОВ
# ==========================================
@bot.message_handler(func=lambda msg: msg.text == "🎁 Промокод")
def enter_promo(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Для начала подпишись на канал!", reply_markup=sub_keyboard())
        return
    msg_wait = bot.send_message(message.chat.id, "✍️ <b>Введите ваш промокод:</b>\n\nОтправь его одним сообщением.", parse_mode="HTML")
    bot.register_next_step_handler(msg_wait, process_promo)

def process_promo(message):
    code = message.text.strip().upper()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT discount, uses_left FROM promocodes WHERE code = ?", (code,))
    promo = cur.fetchone()
    
    if promo and promo[1] > 0:
        discount, uses_left = promo
        cur.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Промокод <b>{code}</b> успешно активирован!\n🎁 Твоя скидка: <b>{discount}%</b>\n\nНапиши менеджеру @pagerNft и укажи этот промокод, чтобы получить скидку.", parse_mode="HTML", reply_markup=get_main_menu())
    else:
        conn.close()
        bot.send_message(message.chat.id, "❌ Такого промокода нет или лимит активаций исчерпан.", reply_markup=get_main_menu())

# ==========================================
# МАГАЗИН
# ==========================================
@bot.message_handler(func=lambda msg: msg.text == "🛒 Купить аккаунты")
def buy_accounts(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Для начала подпишись на канал!", reply_markup=sub_keyboard())
        return
    text = (
        "<b>🛒 Выбери категорию:</b>\n\n"
        "🔹 <b>Обычные аккаунты</b> — покупка количеством, разные страны.\n"
        "✨ <b>Необычные аккаунты</b> — редкие экземпляры поштучно."
    )
    bot.send_message(message.chat.id, text, reply_markup=get_shop_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "💰 Скупка NFT")
def buy_nft(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Для начала подпишись на канал!", reply_markup=sub_keyboard())
        return
    text = (
        "<b>💰 Скупка NFT</b>\n\n"
        "Мы выкупаем NFT-подарки (Gifts) и другие цифровые активы Telegram по выгодным ценам.\n\n"
        "🔹 <b>Что мы скупаем:</b>\n"
        "• Редкие и обычные NFT-подарки.\n"
        "• Номера Telegram.\n"
        "• Юзернеймы.\n\n"
        "💵 <b>Условия:</b>\n"
        "Оценка происходит быстро, оплата моментальная.\n\n"
        "Для оценки свяжитесь с нами:"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("💬 Написать менеджеру", url=f"https://t.me/{MANAGER_USERNAME}"),
        types.InlineKeyboardButton("👑 Написать владельцу", url=f"https://t.me/{OWNER_USERNAME}")
    )
    bot.send_message(message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "📜 Как купить?")
def how_to_buy(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Для начала подпишись на канал!", reply_markup=sub_keyboard())
        return
    text = (
        "<b>📜 Инструкция по покупке</b>\n\n"
        "1. Выбери нужный аккаунт из списка.\n"
        "2. Напиши менеджеру @pagerNft и укажи, что хочешь купить.\n"
        "3. Менеджер подтвердит наличие и назовет цену.\n"
        "4. Оплати удобным способом.\n"
        "5. Получи данные от аккаунта и смени пароль.\n\n"
        "⚠️ <b>Гарантия:</b> 24 часа на вход."
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "ℹ️ О магазине")
def about_shop(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Для начала подпишись на канал!", reply_markup=sub_keyboard())
        return
    text = (
        "<b>ℹ️ О магазине Slawua SHOP</b>\n\n"
        "Мы работаем на рынке цифровых товаров уже несколько лет.\n\n"
        "✅ <b>Гарантии:</b> замена, гарантия 24 часа, анонимность.\n"
        "📌 <b>Почему мы:</b> моментальная выдача, адекватные цены, поддержка 24/7."
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "⭐ Отзывы")
def reviews(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Для начала подпишись на канал!", reply_markup=sub_keyboard())
        return
    text = (
        "<b>⭐ Отзывы наших клиентов</b>\n\n"
        "Все реальные отзывы о нашей работе вы можете посмотреть в нашем официальном канале.\n\n"
        "Нажми на кнопку ниже, чтобы перейти:"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📢 Перейти в канал с отзывами", url=f"https://t.me/{REVIEWS_CHANNEL}"))
    bot.send_message(message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "💬 Связаться с продавцом")
def contact_seller(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Для начала подпишись на канал!", reply_markup=sub_keyboard())
        return
    text = (
        f"👤 <b>По всем вопросам покупки обращайтесь к нашему менеджеру.</b>\n\n"
        f"Владелец магазина: @{OWNER_USERNAME}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Написать менеджеру", url=f"https://t.me/{MANAGER_USERNAME}"))
    kb.add(types.InlineKeyboardButton("👑 Написать владельцу", url=f"https://t.me/{OWNER_USERNAME}"))
    bot.send_message(message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "show_regular")
def show_regular(call):
    text = (
        "<b>🌍 Обычные аккаунты (по странам)</b>\n\n"
        f"{ACCOUNTS_TEXT}\n"
        "──────────────────\n"
        "Для покупки напиши менеджеру: @pagerNft"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Написать менеджеру", url=f"https://t.me/{MANAGER_USERNAME}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_shop"))
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "show_unusual")
def show_unusual(call):
    text = (
        "<b>✨ Необычные аккаунты (поштучно)</b>\n\n"
        f"{FAKE_IDS}\n"
        "──────────────────\n"
        "Для покупки напиши менеджеру: @pagerNft"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Написать менеджеру", url=f"https://t.me/{MANAGER_USERNAME}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_shop"))
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "refresh_stock")
def refresh_stock(call):
    bot.answer_callback_query(call.id, "Наличие обновлено!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_shop")
def back_to_shop(call):
    text = (
        "<b>🛒 Выбери категорию:</b>\n\n"
        "🔹 <b>Обычные аккаунты</b> — покупка количеством.\n"
        "✨ <b>Необычные аккаунты</b> — редкие экземпляры."
    )
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_shop_menu(), parse_mode="HTML")

# ==========================================
# ЗАПУСК
# ==========================================
def run_flask():
    app = Flask(__name__)
    
    @app.route('/')
    def health():
        return "Bot is running"
        
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    init_db()
    print("Slawua SHOP запущен...")
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
