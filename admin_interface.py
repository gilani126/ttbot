import sqlite3
import logging
from telebot import types
from marketplace import cursor, conn
from bot_init import create_bot



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


bot = create_bot()  # Инициализация бота

ADMIN_ID = '6853962237'  # ID админа

# Функция для вызова админ-панели
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.chat.id) == ADMIN_ID:
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
    msg = bot.send_message(call.message.chat.id, "Введите название новой категории:")
    bot.register_next_step_handler(msg, process_new_category)

def process_new_category(message):
    category_name = message.text
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
    conn.commit()
    bot.send_message(message.chat.id, f"Категория '{category_name}' создана.")
    admin_panel(message)

# Создание подкатегории
@bot.callback_query_handler(func=lambda call: call.data == "create_subcategory")
def create_subcategory_handler(call):
    categories = cursor.execute("SELECT * FROM categories").fetchall()
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
    subcategory_name = message.text
    cursor.execute("INSERT INTO subcategories (name, category_id) VALUES (?, ?)", (subcategory_name, category_id))
    conn.commit()
    bot.send_message(message.chat.id, f"Подкатегория '{subcategory_name}' создана.")
    admin_panel(message)

# Редактирование категории
@bot.callback_query_handler(func=lambda call: call.data == "edit_category")
def edit_category_handler(call):
    categories = cursor.execute("SELECT * FROM categories").fetchall()
    markup = types.InlineKeyboardMarkup()
    for category in categories:
        markup.add(types.InlineKeyboardButton(category[1], callback_data=f"edit_category_{category[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите категорию для редактирования:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_category_"))
def category_edit_options(call):
    category_id = call.data.split("_")[2]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Изменить название", callback_data=f"rename_category_{category_id}"))
    markup.add(types.InlineKeyboardButton("Удалить категорию", callback_data=f"delete_category_{category_id}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rename_category_"))
def rename_category(call):
    category_id = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, "Введите новое название категории:")
    bot.register_next_step_handler(msg, lambda m: process_rename_category(m, category_id))

def process_rename_category(message, category_id):
    new_name = message.text
    cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
    conn.commit()
    bot.send_message(message.chat.id, f"Категория переименована в '{new_name}'.")
    admin_panel(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_category_"))
def delete_category(call):
    category_id = call.data.split("_")[2]
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    bot.send_message(call.message.chat.id, "Категория удалена.")
    admin_panel(call.message)

# Редактирование подкатегории
@bot.callback_query_handler(func=lambda call: call.data == "edit_subcategory")
def edit_subcategory_handler(call):
    categories = cursor.execute("SELECT * FROM categories").fetchall()
    markup = types.InlineKeyboardMarkup()
    for category in categories:
        markup.add(types.InlineKeyboardButton(category[1], callback_data=f"select_category_{category[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите категорию:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_category_"))
def select_category_for_subcategory(call):
    category_id = call.data.split("_")[2]
    subcategories = cursor.execute("SELECT * FROM subcategories WHERE category_id = ?", (category_id,)).fetchall()
    markup = types.InlineKeyboardMarkup()
    for sub in subcategories:
        markup.add(types.InlineKeyboardButton(sub[1], callback_data=f"edit_subcategory_{sub[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите подкатегорию для редактирования:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_subcategory_"))
def subcategory_edit_options(call):
    subcategory_id = call.data.split("_")[2]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Изменить название", callback_data=f"rename_subcategory_{subcategory_id}"))
    markup.add(types.InlineKeyboardButton("Удалить подкатегорию", callback_data=f"delete_subcategory_{subcategory_id}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rename_subcategory_"))
def rename_subcategory(call):
    subcategory_id = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, "Введите новое название подкатегории:")
    bot.register_next_step_handler(msg, lambda m: process_rename_subcategory(m, subcategory_id))

def process_rename_subcategory(message, subcategory_id):
    new_name = message.text
    cursor.execute("UPDATE subcategories SET name = ? WHERE id = ?", (new_name, subcategory_id))
    conn.commit()
    bot.send_message(message.chat.id, f"Подкатегория переименована в '{new_name}'.")
    admin_panel(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_subcategory_"))
def delete_subcategory(call):
    subcategory_id = call.data.split("_")[2]
    cursor.execute("DELETE FROM subcategories WHERE id = ?", (subcategory_id,))
    conn.commit()
    bot.send_message(call.message.chat.id, "Подкатегория удалена.")
    admin_panel(call.message)

# Удаление позиции
@bot.callback_query_handler(func=lambda call: call.data == "delete_item")
def delete_item_handler(call):
    categories = cursor.execute("SELECT * FROM categories").fetchall()
    markup = types.InlineKeyboardMarkup()
    for category in categories:
        markup.add(types.InlineKeyboardButton(category[1], callback_data=f"delete_item_category_{category[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите категорию для удаления товара:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_item_category_"))
def delete_item_select_subcategory(call):
    category_id = call.data.split("_")[-1]
    subcategories = cursor.execute("SELECT * FROM subcategories WHERE category_id = ?", (category_id,)).fetchall()
    markup = types.InlineKeyboardMarkup()
    for sub in subcategories:
        markup.add(types.InlineKeyboardButton(sub[1], callback_data=f"delete_item_subcategory_{sub[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите подкатегорию для удаления товара:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_item_subcategory_"))
def delete_item_select_item(call):
    subcategory_id = call.data.split("_")[-1]
    items = cursor.execute("SELECT * FROM items WHERE subcategory_id = ?", (subcategory_id,)).fetchall()
    markup = types.InlineKeyboardMarkup()
    for item in items:
        markup.add(types.InlineKeyboardButton(item[1], callback_data=f"delete_item_confirm_{item[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Выберите товар для удаления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_item_confirm_"))
def delete_item_confirmation(call):
    item_id = call.data.split("_")[-1]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Подтвердить удаление", callback_data=f"delete_item_final_{item_id}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="admin_cancel"))
    bot.send_message(call.message.chat.id, "Вы уверены, что хотите удалить этот товар?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_item_final_"))
def delete_item_final(call):
    item_id = call.data.split("_")[-1]
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    bot.send_message(call.message.chat.id, "Товар успешно удален.")
    admin_panel(call.message)
