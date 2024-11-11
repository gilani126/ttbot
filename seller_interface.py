from bot_init import create_bot
from telebot import types
import logging
import sqlite3

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', mode='a')
    ]
)

bot = create_bot()
admin_chat_id = '6853962237'  # Замените на ID вашего администратора

def get_db_connection():
    """Создаёт новое подключение к базе данных SQLite."""
    conn = sqlite3.connect('marketplace.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Статусы
WAITING_CATEGORY = 1
WAITING_SUBCATEGORY = 2
WAITING_ITEM_NAME = 3
WAITING_ITEM_PRICE = 4
WAITING_ITEM_DESCRIPTION = 5
WAITING_ITEM_CONTENT = 6
WAITING_ADMIN_APPROVAL = 7

user_data = {}

def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 Я хочу купить"), types.KeyboardButton("💼 Я хочу продать"))
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💼 Я хочу продать")
def handle_sell(message):
    user_data[message.chat.id] = {'step': WAITING_CATEGORY}
    show_categories(message)

def show_categories(message):
    with get_db_connection() as conn:
        categories = conn.execute("SELECT * FROM categories").fetchall()
        if categories:
            markup = types.InlineKeyboardMarkup()
            for category in categories:
                markup.add(types.InlineKeyboardButton(category["name"], callback_data=f"category_{category['id']}"))
            bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Категории не найдены.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def choose_category(call):
    category_id = call.data.split("_")[1]
    user_data[call.message.chat.id]['category_id'] = category_id
    user_data[call.message.chat.id]['step'] = WAITING_SUBCATEGORY
    show_subcategories(call.message, category_id)

def show_subcategories(message, category_id):
    with get_db_connection() as conn:
        subcategories = conn.execute("SELECT * FROM subcategories WHERE category_id = ?", (category_id,)).fetchall()
        if subcategories:
            markup = types.InlineKeyboardMarkup()
            for subcategory in subcategories:
                markup.add(types.InlineKeyboardButton(subcategory["name"], callback_data=f"subcategory_{subcategory['id']}"))
            bot.send_message(message.chat.id, "Выберите подкатегорию:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Подкатегории не найдены.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("subcategory_"))
def choose_subcategory(call):
    subcategory_id = call.data.split("_")[1]
    user_data[call.message.chat.id]['subcategory_id'] = subcategory_id
    user_data[call.message.chat.id]['step'] = WAITING_ITEM_NAME
    bot.send_message(call.message.chat.id, "Введите название товара:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('step') == WAITING_ITEM_NAME)
def handle_item_name(message):
    user_data[message.chat.id]['item_name'] = message.text
    user_data[message.chat.id]['step'] = WAITING_ITEM_PRICE
    bot.send_message(message.chat.id, "Введите цену товара:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('step') == WAITING_ITEM_PRICE)
def handle_item_price(message):
    try:
        price = float(message.text)
        user_data[message.chat.id]['item_price'] = price
        user_data[message.chat.id]['step'] = WAITING_ITEM_DESCRIPTION
        bot.send_message(message.chat.id, "Введите описание товара:")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную цену.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('step') == WAITING_ITEM_DESCRIPTION)
def handle_item_description(message):
    user_data[message.chat.id]['item_description'] = message.text
    user_data[message.chat.id]['step'] = WAITING_ITEM_CONTENT
    bot.send_message(message.chat.id, "Отправьте содержимое товара. Вы можете отправить фото и описание. Когда закончите, нажмите 'Описание Готово'.")

@bot.message_handler(content_types=['photo', 'text'], func=lambda message: user_data.get(message.chat.id, {}).get('step') == WAITING_ITEM_CONTENT)
def handle_item_content(message):
    if message.text == "Описание Готово":
        # Сохраняем товар на рассмотрение администратору
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO items (name, price, description, subcategory_id, approved)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_data[message.chat.id]['item_name'],
                user_data[message.chat.id]['item_price'],
                user_data[message.chat.id]['item_description'],
                user_data[message.chat.id]['subcategory_id'],
                0  # Товар на рассмотрении
            ))
            conn.commit()

        # Отправляем администратору
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Одобрить", callback_data="approve"), types.InlineKeyboardButton("Отклонить", callback_data="reject"))
        bot.send_message(admin_chat_id, f"Новый товар на рассмотрении:\n\n"
                                       f"Категория: {user_data[message.chat.id]['category_id']}\n"
                                       f"Подкатегория: {user_data[message.chat.id]['subcategory_id']}\n"
                                       f"Название: {user_data[message.chat.id]['item_name']}\n"
                                       f"Цена: {user_data[message.chat.id]['item_price']}₽\n"
                                       f"Описание: {user_data[message.chat.id]['item_description']}",
                         reply_markup=markup)

        bot.send_message(message.chat.id, "Товар отправлен на рассмотрение администратору.")

@bot.callback_query_handler(func=lambda call: call.data == "approve")
def approve_item(call):
    # Одобрение товара
    bot.send_message(admin_chat_id, "Товар одобрен.")
    bot.send_message(call.message.chat.id, "Ваш товар одобрен. Он теперь доступен в каталоге.")
    # Здесь можно обновить запись в БД, чтобы товар был доступен для продажи

@bot.callback_query_handler(func=lambda call: call.data == "reject")
def reject_item(call):
    bot.send_message(admin_chat_id, "Товар отклонен.")
    bot.send_message(call.message.chat.id, "Ваш товар отклонен. Напишите причину отклонения.")
    user_data[call.message.chat.id]['step'] = WAITING_ITEM_DESCRIPTION

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('step') == WAITING_ITEM_DESCRIPTION)
def handle_rejection_reason(message):
    reason = message.text
    bot.send_message(message.chat.id, f"Причина отклонения: {reason}")
    bot.send_message(admin_chat_id, f"Причина отклонения товара: {reason}")
    bot.send_message(message.chat.id, "Причина отклонения отправлена администратору.")
