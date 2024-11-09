import sqlite3
import logging
from bot_init import create_bot
from buyer_interface import start, show_categories, show_subcategories, show_items, handle_item_purchase
from admin_interface import admin_panel

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', mode='a')
    ]
)

# Инициализация бота
bot = create_bot()

# Удаляем вебхук
bot.remove_webhook()

# Функция для выполнения запросов в БД
def execute_query(query, params=()):
    try:
        with sqlite3.connect('marketplace.db') as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Ошибка базы данных: {e}")
        return None

@bot.message_handler(commands=['start'])
def handle_start(message):
    start(message)

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    admin_panel(message)

@bot.message_handler(func=lambda message: message.text == "🛒 Я хочу купить")
def handle_buy(message):
    categories = execute_query("SELECT * FROM categories")
    if not categories:
        bot.send_message(message.chat.id, "Нет доступных категорий. Пожалуйста, создайте категорию через администратора.")
        return
    show_categories(message)

@bot.message_handler(func=lambda message: message.text == "💼 Я хочу продать")
def handle_sell(message):
    categories = execute_query("SELECT * FROM categories")
    if not categories:
        bot.send_message(message.chat.id, "Нет доступных категорий. Пожалуйста, создайте категорию через администратора.")
        return
    show_categories(message)

# Обработка категорий, подкатегорий, товаров
@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def handle_category(call):
    try:
        category_id = int(call.data.split('_')[1])
        show_subcategories(call.message, category_id)
    except ValueError:
        bot.send_message(call.message.chat.id, "Неверный формат данных категории.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("subcategory_"))
def handle_subcategory(call):
    try:
        subcategory_id = int(call.data.split('_')[1])
        show_items(call.message, subcategory_id)
    except ValueError:
        bot.send_message(call.message.chat.id, "Неверный формат данных подкатегории.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("item_"))
def handle_item(call):
    try:
        item_id = int(call.data.split('_')[1])
        handle_item_purchase(call.message, item_id)
    except ValueError:
        bot.send_message(call.message.chat.id, "Неверный формат данных товара.")

# Старт бота
bot.polling(none_stop=True, interval=0, timeout=1000)
