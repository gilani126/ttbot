from bot_init import create_bot  # Import the function to create the bot
from buyer_interface import start, show_categories, show_subcategories, show_items, handle_item_purchase
from admin_interface import admin_panel
from marketplace import conn, cursor
import sqlite3  # Import sqlite3 for database operations
import logging 

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования (DEBUG - самый подробный, ERROR - только ошибки)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат вывода сообщений
    handlers=[
        logging.StreamHandler(),  # Вывод логов в консоль
        logging.FileHandler('bot.log', mode='a')  # Логи также сохраняются в файл 'bot.log'
    ]
)

# Пример использования
logging.debug("Это сообщение для отладки")
logging.info("Это информационное сообщение")
logging.warning("Это предупреждение")
logging.error("Произошла ошибка!")
logging.critical("Это критическая ошибка!")


# Initialize the bot object
bot = create_bot()

# Initialize the database connection and cursor
conn = sqlite3.connect('marketplace.db', check_same_thread=False)
cursor = conn.cursor()

@bot.message_handler(commands=['start'])
def handle_start(message):
    start(message)

# Удаляем вебхук
bot.remove_webhook()

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    admin_panel(message)

@bot.message_handler(func=lambda message: message.text == "🛒 Я хочу купить")
def handle_buy(message):
    try:
        categories = cursor.execute("SELECT * FROM categories").fetchall()
        if not categories:
            bot.send_message(message.chat.id, "Нет доступных категорий. Пожалуйста, создайте категорию через администратора.")
            return
        show_categories(message)
    except sqlite3.Error as e:
        bot.send_message(message.chat.id, f"Ошибка базы данных: {e}")

@bot.message_handler(func=lambda message: message.text == "💼 Я хочу продать")
def handle_sell(message):
    try:
        categories = cursor.execute("SELECT * FROM categories").fetchall()
        if not categories:
            bot.send_message(message.chat.id, "Нет доступных категорий. Пожалуйста, создайте категорию через администратора.")
            return
        show_categories(message, cursor)
    except sqlite3.Error as e:
        bot.send_message(message.chat.id, f"Ошибка базы данных: {e}")

# Handling categories, subcategories, items
@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def handle_category(call):
    try:
        category_id = int(call.data.split('_')[1])
        show_subcategories(call.message, category_id, cursor)
    except ValueError:
        bot.send_message(call.message.chat.id, "Неверный формат данных категории.")
    except sqlite3.Error as e:
        bot.send_message(call.message.chat.id, f"Ошибка базы данных: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("subcategory_"))
def handle_subcategory(call):
    try:
        subcategory_id = int(call.data.split('_')[1])
        show_items(call.message, subcategory_id, cursor)
    except ValueError:
        bot.send_message(call.message.chat.id, "Неверный формат данных подкатегории.")
    except sqlite3.Error as e:
        bot.send_message(call.message.chat.id, f"Ошибка базы данных: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("item_"))
def handle_item(call):
    try:
        item_id = int(call.data.split('_')[1])
        handle_item_purchase(call.message, item_id, cursor)
    except ValueError:
        bot.send_message(call.message.chat.id, "Неверный формат данных товара.")
    except sqlite3.Error as e:
        bot.send_message(call.message.chat.id, f"Ошибка базы данных: {e}")

        logging.debug 

# Start the bot
bot.polling(none_stop=True, interval=0, timeout=1000)
