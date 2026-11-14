import telebot
from telebot import types
import sqlite3
import time

# ==========================================
# НАСТРОЙКИ
# ==========================================
BOT_TOKEN = ""
DB_NAME = "giveaway.db"
OWNER_ID = 7425512449  # Твой ID
OWNER_USERNAME = "@killedrax"  # Твой юзернейм

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# БАЗА ДАННЫХ
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            chat_id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 0,
            total_winners INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def activate_giveaway(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO giveaways (chat_id, count, total_winners, is_active) VALUES (?, 0, 0, 1)", (chat_id,))
    conn.commit()
    conn.close()

def get_counter(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT count, total_winners, is_active FROM giveaways WHERE chat_id = ?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return row if row else (0, 0, 0)

def update_counter(chat_id, count, winners):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE giveaways SET count = ?, total_winners = ? WHERE chat_id = ?", (count, winners, chat_id))
    conn.commit()
    conn.close()

# ==========================================
# ПРИЗЫ ПО КУБИКУ
# ==========================================
PRIZES = {
    1: "🌹 Роза",
    2: "💐 Букет",
    3: "💍 Кольцо",
    4: "🧸 Мишка",
    5: "❤️ Сердце",
    6: "💎 Алмаз"
}

# ==========================================
# КОМАНДЫ
# ==========================================
@bot.message_handler(commands=['start'])
def start_handler(message):
    text = "Напиши /start_giveaway в чате, где хочешь запустить розыгрыш."
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['start_giveaway'])
def start_giveaway(message):
    if message.chat.type not in ['group', 'supergroup']:
        return
        
    try:
        admins = [a.user.id for a in bot.get_chat_administrators(message.chat.id)]
        if message.from_user.id not in admins:
            return
    except Exception:
        return

    text = (
        "🎁 <b>РОЗЫГРЫШ ЗАПУЩЕН!</b>\n\n"
        "Каждый <b>77-й комментарий</b> получает подарок!\n"
        "Бот сам кинет кубик и определит, какой приз достанется победителю. 🎲"
    )
    msg = bot.send_message(message.chat.id, text, parse_mode="HTML")
    try:
        bot.pin_chat_message(message.chat.id, msg.message_id, disable_notification=True)
    except Exception:
        pass
    activate_giveaway(message.chat.id)

# ==========================================
# СЧЕТЧИК СООБЩЕНИЙ
# ==========================================
@bot.message_handler(func=lambda message: True)
def count_messages(message):
    if message.text and message.text.startswith('/'):
        return
    if message.from_user and message.from_user.is_bot:
        return
        
    count, winners, is_active = get_counter(message.chat.id)
    if not is_active:
        return
        
    new_count = count + 1
    
    if new_count >= 77:
        # 1. Фиксируем победителя и сбрасываем счетчик
        winners += 1
        update_counter(message.chat.id, 0, winners)
        
        winner_mention = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        
        # 2. Бот кидает кубик
        dice_msg = bot.send_dice(message.chat.id, emoji="🎲")
        
        # 3. Ждем, пока кубик прокрутится (4 секунды)
        time.sleep(4)
        
        # 4. Получаем значение кубика и приз
        dice_value = dice_msg.dice.value
        prize = PRIZES.get(dice_value, "Неизвестный приз")
        
        # 5. Пишем результат в чат
        chat_text = (
            f"🎉 <b>ПОБЕДИТЕЛЬ №{winners}!</b> 🎉\n\n"
            f"77-й комментарий оставил: <b>{winner_mention}</b>!\n\n"
            f"Кубик выбросил <b>{dice_value}</b>, и победитель получает:\n"
            f"🎁 <b>{prize}</b>\n\n"
            f"Владелец {OWNER_USERNAME} свяжется с тобой. Поздравляем!"
        )
        bot.send_message(message.chat.id, chat_text, parse_mode="HTML")
        
        # 6. Закрепляем сообщение победителя
        try:
            bot.pin_chat_message(message.chat.id, message.message_id, disable_notification=False)
        except Exception:
            pass
            
        # 7. Отправляем уведомление тебе в личку
        owner_text = (
            f"🔔 <b>НОВЫЙ ПОБЕДИТЕЛЬ В ЧАТЕ!</b>\n\n"
            f"Чат: <b>{message.chat.title}</b>\n"
            f"Победитель: <b>{winner_mention}</b>\n"
            f"Выпало число: <b>{dice_value}</b>\n"
            f"Приз: <b>{prize}</b>\n\n"
            f"Зайди в чат и выдай подарок!"
        )
        try:
            bot.send_message(OWNER_ID, owner_text, parse_mode="HTML")
        except Exception as e:
            print(f"Не удалось отправить сообщение владельцу: {e}")

    else:
        update_counter(message.chat.id, new_count, winners)

# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    init_db()
    print("Бот запущен. Жду 77 сообщений...")
    bot.infinity_polling()
