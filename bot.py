import telebot
from telebot import types
import sqlite3
import time
import os
import threading
import random
from flask import Flask

# ==========================================
# НАСТРОЙКИ
# ==========================================
BOT_TOKEN = "9052843841:AAGZPiN0Zu4-QfZoQkXvLCZQo2y2aEfCaAg"
DB_NAME = "giveaway.db"
OWNER_ID = 7425512449
OWNER_USERNAME = "@killedrax"

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
# ПРИЗЫ
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
        "Бот сам кинет кубик и определит приз. 🎲\n\n"
        "🔥 <b>Внимание:</b> если выпадет 6, судьба решит, что ты получишь: Алмаз или <b>NFT-подарок</b>!"
    )
    msg = bot.send_message(message.chat.id, text, parse_mode="HTML")
    try:
        bot.pin_chat_message(message.chat.id, msg.message_id, disable_notification=True)
    except Exception:
        pass
    activate_giveaway(message.chat.id)

# ==========================================
# РУЧНАЯ ВЫДАЧА NFT (ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА)
# ==========================================
@bot.message_handler(commands=['give_nft'])
def give_nft(message):
    if message.from_user.id != OWNER_ID:
        return
        
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Формат: /give_nft @username или ID\nПример: /give_nft @vasek122")
            return
            
        target = args[1]
        
        text = (
            f"🎁 <b>ПОЗДРАВЛЯЕМ!</b>\n\n"
            f"Владелец магазина только что подарил тебе <b>NFT-подарок</b>!\n\n"
            f"Напиши мне (@{OWNER_USERNAME}) в личку, и я передам тебе твой NFT."
        )
        
        if target.startswith('@'):
            bot.send_message(message.chat.id, f"✅ Уведомление отправлено пользователю {target}.", parse_mode="HTML")
            bot.send_message(message.chat.id, text, parse_mode="HTML")
        else:
            try:
                target_id = int(target)
                bot.send_message(target_id, text, parse_mode="HTML")
                bot.reply_to(message, "✅ NFT успешно отправлен в личку пользователю!")
            except Exception as e:
                bot.reply_to(message, f"❌ Ошибка: {e}")
                
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ==========================================
# СЧЕТЧИК
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
        winners += 1
        update_counter(message.chat.id, 0, winners)
        
        winner_mention = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        winner_id = message.from_user.id
        
        dice_msg = bot.send_dice(message.chat.id, emoji="🎲")
        time.sleep(4)
        
        dice_value = dice_msg.dice.value
        
        # Логика: если выпало 6, рандомим между Алмазом и NFT
        if dice_value == 6:
            if random.choice([True, False]):
                prize = "🎁 NFT-подарок!"
                chat_text = (
                    f"🎉 <b>ДЖЕКПОТ! ПОБЕДИТЕЛЬ №{winners}!</b> 🎉\n\n"
                    f"77-й комментарий оставил: <b>{winner_mention}</b>!\n\n"
                    f"Кубик выбросил <b>6</b>, и фортуна решила, что победитель получает:\n"
                    f"🎁 <b>{prize}</b>\n\n"
                    f"Владелец {OWNER_USERNAME} свяжется с тобой для выдачи NFT!"
                )
            else:
                prize = "💎 Алмаз (без NFT)"
                chat_text = (
                    f"🎉 <b>ПОБЕДИТЕЛЬ №{winners}!</b> 🎉\n\n"
                    f"77-й комментарий оставил: <b>{winner_mention}</b>!\n\n"
                    f"Кубик выбросил <b>6</b>, но фортуна решила, что сегодня ты получаешь:\n"
                    f"🎁 <b>{prize}</b>\n\n"
                    f"Владелец {OWNER_USERNAME} свяжется с тобой."
                )
        else:
            prize = PRIZES.get(dice_value, "Неизвестный приз")
            chat_text = (
                f"🎉 <b>ПОБЕДИТЕЛЬ №{winners}!</b> 🎉\n\n"
                f"77-й комментарий оставил: <b>{winner_mention}</b>!\n\n"
                f"Кубик выбросил <b>{dice_value}</b>, и победитель получает:\n"
                f"🎁 <b>{prize}</b>\n\n"
                f"Владелец {OWNER_USERNAME} свяжется с тобой. Поздравляем!"
            )
            
        bot.send_message(message.chat.id, chat_text, parse_mode="HTML")
        
        try:
            bot.pin_chat_message(message.chat.id, message.message_id, disable_notification=False)
        except Exception:
            pass
            
        owner_text = (
            f"🔔 <b>НОВЫЙ ПОБЕДИТЕЛЬ!</b>\n\n"
            f"Чат: <b>{message.chat.title}</b>\n"
            f"Победитель: <b>{winner_mention}</b> (ID: <code>{winner_id}</code>)\n"
            f"Выпало: <b>{dice_value}</b>\n"
            f"Приз: <b>{prize}</b>\n\n"
        )
        
        if "NFT" in prize:
            owner_text += f"⚠️ <b>ВНИМАНИЕ!</b> Выпал NFT. Чтобы выдать его, напиши:\n<code>/give_nft {winner_id}</code>"
            
        try:
            bot.send_message(OWNER_ID, owner_text, parse_mode="HTML")
        except Exception:
            pass
    else:
        update_counter(message.chat.id, new_count, winners)

# ==========================================
# ВЕБ-СЕРВЕР ДЛЯ RENDER
# ==========================================
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    init_db()
    print("Запуск бота и веб-сервера...")
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
