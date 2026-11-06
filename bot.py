import telebot
from telebot import types
from flask import Flask
import threading
import os

# ==========================================
# НАСТРОЙКИ
# ==========================================
BOT_TOKEN = "9104960855:AAHa8wTH_Gq58lO-jUCTn4cnDIOR7lWZjMA"
MANAGER_USERNAME = "pagerNft"     # Менеджер
OWNER_USERNAME = "Slawua_shop"    # Владелец
REVIEWS_CHANNEL = "otzivi_slawua" # Канал с отзывами

bot = telebot.TeleBot(BOT_TOKEN)

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
        types.KeyboardButton("💬 Связаться с продавцом")
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
# ХЕНДЛЕРЫ
# ==========================================
@bot.message_handler(commands=['start'])
def start_handler(message):
    text = (
        "<b>Slawua SHOP</b> 🛍\n\n"
        "Добро пожаловать в наш магазин Telegram-аккаунтов и NFT!\n\n"
        "Мы предлагаем качественные аккаунты из разных стран, а также скупаем и продаем NFT.\n\n"
        "Выбери нужный раздел в меню ниже, чтобы начать."
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "🛒 Купить аккаунты")
def buy_accounts(message):
    text = (
        "<b>🛒 Выбери категорию:</b>\n\n"
        "🔹 <b>Обычные аккаунты</b> — покупка количеством, разные страны.\n"
        "✨ <b>Необычные аккаунты</b> — редкие экземпляры поштучно (большая отлега, редкое гео и т.д.)."
    )
    bot.send_message(message.chat.id, text, reply_markup=get_shop_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "💰 Скупка NFT")
def buy_nft(message):
    text = (
        "<b>💰 Скупка NFT</b>\n\n"
        "Мы выкупаем NFT-подарки (Gifts) и другие цифровые активы Telegram по выгодным ценам.\n\n"
        "🔹 <b>Что мы скупаем:</b>\n"
        "• Редкие и обычные NFT-подарки.\n"
        "• Номера Telegram.\n"
        "• Юзернеймы.\n\n"
        "💵 <b>Условия:</b>\n"
        "Оценка происходит быстро, оплата моментальная. Выкупаем как мелкие, так и крупные лоты.\n\n"
        "Для оценки свяжитесь с нами:"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("💬 Написать менеджеру", url=f"https://t.me/{MANAGER_USERNAME}"),
        types.InlineKeyboardButton("👑 Написать владельцу", url=f"https://t.me/{OWNER_USERNAME}")
    )
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
    bot.answer_callback_query(call.id, "Наличие обновлено! Все аккаунты в списке актуальны.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_shop")
def back_to_shop(call):
    text = (
        "<b>🛒 Выбери категорию:</b>\n\n"
        "🔹 <b>Обычные аккаунты</b> — покупка количеством, разные страны.\n"
        "✨ <b>Необычные аккаунты</b> — редкие экземпляры поштучно."
    )
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_shop_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "📜 Как купить?")
def how_to_buy(message):
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
    text = (
        "<b>ℹ️ О магазине Slawua SHOP</b>\n\n"
        "Мы работаем на рынке цифровых товаров уже несколько лет. Предлагаем только качественные аккаунты с живыми физическими номерами и выкупаем NFT.\n\n"
        "✅ <b>Наши гарантии:</b>\n"
        "• Замена при неверных данных.\n"
        "• Гарантия на вход 24 часа.\n"
        "• Анонимность и безопасность.\n\n"
        "📌 <b>Почему мы?</b>\n"
        "• Моментальная выдача после оплаты.\n"
        "• Адекватные цены.\n"
        "• Поддержка 24/7."
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "⭐ Отзывы")
def reviews(message):
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
    text = (
        f"👤 <b>По всем вопросам покупки обращайтесь к нашему менеджеру.</b>\n\n"
        f"Владелец магазина: @{OWNER_USERNAME}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Написать менеджеру", url=f"https://t.me/{MANAGER_USERNAME}"))
    kb.add(types.InlineKeyboardButton("👑 Написать владельцу", url=f"https://t.me/{OWNER_USERNAME}"))
    bot.send_message(message.chat.id, text, reply_markup=kb, parse_mode="HTML")

# ==========================================
# ЗАПУСК (ФЛАСК ДЛЯ RENDER)
# ==========================================
def run_flask():
    app = Flask(__name__)
    
    @app.route('/')
    def health():
        return "Bot is running"
        
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    print("Slawua SHOP запущен...")
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
