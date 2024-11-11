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

def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 Я хочу купить"), types.KeyboardButton("💼 Я хочу продать"))
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

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

def show_items(message, subcategory_id):
    with get_db_connection() as conn:
        items = conn.execute("SELECT * FROM items WHERE subcategory_id = ?", (subcategory_id,)).fetchall()
        if items:
            markup = types.InlineKeyboardMarkup()
            for item in items:
                markup.add(types.InlineKeyboardButton(f"{item['name']} - {item['price']}₽", callback_data=f"item_{item['id']}"))
            bot.send_message(message.chat.id, "Выберите товар для покупки:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Товары не найдены.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("item_"))
def handle_item_purchase(call):
    item_id = call.data.split("_")[1]
    with get_db_connection() as conn:
        item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if item:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("💳 Банковский перевод"))
            markup.add(types.KeyboardButton("💰 Криптовалюта (USDT TRC20)"))
            markup.add(types.KeyboardButton("💵 Наличные"))
            bot.send_message(call.message.chat.id, f"Вы выбрали товар: {item['name']}. Цена: {item['price']}₽. Завершить покупку?",
                             reply_markup=markup)
            bot.register_next_step_handler(call.message, handle_payment_choice, item)
        else:
            bot.send_message(call.message.chat.id, "Товар не найден.")

def handle_payment_choice(message, item):
    try:
        if message.text == "💳 Банковский перевод":
            bot.send_message(message.chat.id, "Реквизиты для банковского перевода: ...")
        elif message.text == "💰 Криптовалюта (USDT TRC20)":
            bot.send_message(message.chat.id, "Реквизиты для криптовалюты USDT TRC20: ...")
        elif message.text == "💵 Наличные":
            bot.send_message(message.chat.id, "Договоритесь с продавцом о встрече для оплаты наличными.")

        bot.send_message(message.chat.id, "Нажмите 'Я оплатил' после того, как выполните платеж.")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Я оплатил"))
        bot.send_message(message.chat.id, "Ожидаю подтверждения оплаты.", reply_markup=markup)
    except Exception as e:
        logging.error(f"Ошибка при обработке выбора способа оплаты: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
