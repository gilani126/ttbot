import sqlite3
import logging
from telebot import types
from marketplace import cursor, conn  # Импортируем из marketplace.py
from bot_init import create_bot  # Импортируем функцию для создания бота

bot = create_bot()  # Инициализируем объект бота

ADMIN_ID = '6853962237'  # Замените на ID вашего администратора

# Функция для проверки, является ли пользователь администратором
def is_admin(message):
    return str(message.chat.id) == ADMIN_ID

# Проверка существования таблиц в базе данных
def check_tables_exist():
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories';")
        categories_exists = cursor.fetchone()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subcategories';")
        subcategories_exists = cursor.fetchone()
        logging.debug(f"Таблицы exist: {categories_exists}, {subcategories_exists}")
        return categories_exists and subcategories_exists
    except sqlite3.Error as e:
        logging.error(f"Ошибка при проверке таблиц: {e}")
        return False


# Функция для вызова админ-панели
def admin_panel(message):
    if is_admin(message):
        if not check_tables_exist():
            bot.send_message(message.chat.id, "Необходимо создать таблицы для категорий и подкатегорий. Пожалуйста, создайте их и повторите попытку.")
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Создать категорию", callback_data="create_category"))
        markup.add(types.InlineKeyboardButton("Создать подкатегорию", callback_data="create_subcategory"))
        markup.add(types.InlineKeyboardButton("Редактировать категорию", callback_data="edit_category"))
        markup.add(types.InlineKeyboardButton("Редактировать подкатегорию", callback_data="edit_subcategory"))
        markup.add(types.InlineKeyboardButton("Удалить позицию", callback_data="delete_item"))
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для доступа к этому разделу.")

# Обработчик для отмены действия
@bot.callback_query_handler(func=lambda call: call.data == "admin_cancel")
def cancel_action_handler(call):
    bot.send_message(call.message.chat.id, "Действие отменено.")
    admin_panel(call.message)

# Создание категории
@bot.callback_query_handler(func=lambda call: call.data == "create_category")
def create_category_handler(call):
    logging.debug(f"Обрабатывается запрос на создание категории: {call.data}")
    msg = bot.send_message(call.message.chat.id, "Введите название новой категории:")
    bot.register_next_step_handler(msg, process_new_category)

def process_new_category(message):
    try:
        category_name = message.text
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
        conn.commit()
        bot.send_message(message.chat.id, f"Категория '{category_name}' создана.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании категории: {e}")
    admin_panel(message)

# Создание подкатегории
@bot.callback_query_handler(func=lambda call: call.data == "create_subcategory")
def create_subcategory_handler(call):
    if not check_tables_exist():
        bot.send_message(call.message.chat.id, "Таблицы категорий или подкатегорий отсутствуют. Пожалуйста, создайте их.")
        return
    
    categories = cursor.execute("SELECT * FROM categories").fetchall()
    if not categories:
        bot.send_message(call.message.chat.id, "Нет доступных категорий для создания подкатегории. Пожалуйста, создайте категории сначала.")
        return

    markup = types.InlineKeyboardMarkup()
    for category in categories:
        markup.add(types.InlineKeyboardButton(category[1], callback_data=f"choose_category_{category[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите категорию для подкатегории:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_category_"))
def choose_category_for_subcategory(call):
    category_id = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, "Введите название подкатегории:")
    bot.register_next_step_handler(msg, lambda m: process_new_subcategory(m, category_id))

def process_new_subcategory(message, category_id):
    try:
        subcategory_name = message.text
        cursor.execute("INSERT INTO subcategories (name, category_id) VALUES (?, ?)", (subcategory_name, category_id))
        conn.commit()
        bot.send_message(message.chat.id, f"Подкатегория '{subcategory_name}' создана.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании подкатегории: {e}")
    admin_panel(message)

# Редактирование категории
@bot.callback_query_handler(func=lambda call: call.data == "edit_category")
def edit_category_handler(call):
    if not check_tables_exist():
        bot.send_message(call.message.chat.id, "Таблицы категорий отсутствуют. Пожалуйста, создайте их.")
        return
    
    categories = cursor.execute("SELECT * FROM categories").fetchall()
    markup = types.InlineKeyboardMarkup()
    for category in categories:
        markup.add(types.InlineKeyboardButton(category[1], callback_data=f"edit_category_{category[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите категорию для редактирования:", reply_markup=markup)

# Обработка старта
@bot.message_handler(commands=['start'])
def start(message):
    if is_admin(message):
        admin_panel(message)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для доступа к этому разделу.")