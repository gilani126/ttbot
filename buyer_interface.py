from bot_init import create_bot  # Импортируем функцию для создания бота
from marketplace import cursor, conn

from telebot import types
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


bot = create_bot()  # Инициализируем бота

admin_chat_id = '6853962237'  # Замените на ID вашего администратора


# Сценарий 1: Я хочу купить

def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 Я хочу купить"))
    markup.add(types.KeyboardButton("💼 Я хочу продать"))
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

def show_categories(message, cursor):
    try:
        categories = cursor.execute("SELECT * FROM categories").fetchall()
        if not categories:
            bot.send_message(message.chat.id, "Категории не найдены.")
            return
        inline_markup = types.InlineKeyboardMarkup()
        for category in categories:
            inline_markup.add(types.InlineKeyboardButton(category[1], callback_data=f"category_{category[0]}"))
        bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=inline_markup)
    except Exception as e:
        logging.error(f"Ошибка при получении категорий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

def show_subcategories(message, category_id, cursor):
    try:
        subcategories = cursor.execute("SELECT * FROM subcategories WHERE category_id = ?", (category_id,)).fetchall()
        if not subcategories:
            bot.send_message(message.chat.id, "Подкатегории не найдены.")
            return
        inline_markup = types.InlineKeyboardMarkup()
        for subcategory in subcategories:
            inline_markup.add(types.InlineKeyboardButton(subcategory[1], callback_data=f"subcategory_{subcategory[0]}"))
        bot.send_message(message.chat.id, "Выберите подкатегорию:", reply_markup=inline_markup)
    except Exception as e:
        logging.error(f"Ошибка при получении подкатегорий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

def show_items(message, subcategory_id, cursor):
    try:
        items = cursor.execute("SELECT * FROM items WHERE subcategory_id = ?", (subcategory_id,)).fetchall()
        if not items:
            bot.send_message(message.chat.id, "Товары не найдены.")
            return
        inline_markup = types.InlineKeyboardMarkup()
        for item in items:
            inline_markup.add(types.InlineKeyboardButton(f"{item[1]} - {item[3]}₽", callback_data=f"item_{item[0]}"))
        bot.send_message(message.chat.id, "Выберите товар для покупки:", reply_markup=inline_markup)
    except Exception as e:
        logging.error(f"Ошибка при получении товаров: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

def handle_item_purchase(message, item_id, cursor):
    try:
        item = cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if item:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("💳 Банковский перевод"))
            markup.add(types.KeyboardButton("💰 Криптовалюта (USDT TRC20)"))
            markup.add(types.KeyboardButton("💵 Наличные"))
            bot.send_message(message.chat.id, f"Вы выбрали товар: {item[1]}. Цена: {item[3]}₽. Завершить покупку?",
                             reply_markup=markup)

            # Обработка выбора оплаты
            bot.register_next_step_handler(message, handle_payment_choice, item)
        else:
            bot.send_message(message.chat.id, "Товар не найден.")
    except Exception as e:
        logging.error(f"Ошибка при обработке покупки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

def handle_payment_choice(message, item, cursor):
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

# Сценарий 2: Я хочу продать

# Сценарий 2: Я хочу продать

def handle_sell(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Заполнить информацию о товаре"))
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

def handle_item_info(message):
    # Запрос категории и подкатегории
    bot.send_message(message.chat.id, "Выберите категорию для товара.")
    show_categories(message)  # Показываем категории

def show_categories(message):
    # Получаем все категории из базы данных
    categories = cursor.execute("SELECT * FROM categories").fetchall()
    markup = create_category_buttons(categories)
    bot.send_message(message.chat.id, "Выберите категорию для товара:", reply_markup=markup)

def create_category_buttons(categories, cancel_action="admin_cancel"):
    markup = types.InlineKeyboardMarkup()
    for category in categories:
        markup.add(types.InlineKeyboardButton(category[1], callback_data=f"choose_category_{category[0]}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data=cancel_action))
    return markup

# Обработка выбора категории
@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_category_"))
def choose_category(call):
    category_id = call.data.split("_")[2]
    # Теперь показываем подкатегории для выбранной категории
    show_subcategories(call.message, category_id)

def show_subcategories(message, category_id):
    # Получаем подкатегории для выбранной категории
    subcategories = cursor.execute("SELECT * FROM subcategories WHERE category_id=?", (category_id,)).fetchall()
    if subcategories:
        markup = create_subcategory_buttons(subcategories, category_id)
        bot.send_message(message.chat.id, "Выберите подкатегорию для товара:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "В этой категории нет подкатегорий. Пожалуйста, выберите другую категорию.")

def create_subcategory_buttons(subcategories, category_id, cancel_action="admin_cancel"):
    markup = types.InlineKeyboardMarkup()
    for subcategory in subcategories:
        markup.add(types.InlineKeyboardButton(subcategory[1], callback_data=f"choose_subcategory_{subcategory[0]}_{category_id}"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data=cancel_action))
    return markup

# Обработка выбора подкатегории
@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_subcategory_"))
def choose_subcategory(call):
    subcategory_id, category_id = call.data.split("_")[2], call.data.split("_")[3]
    # Переходим к сбору информации о товаре
    collect_item_details(call.message, category_id, subcategory_id)

def collect_item_details(message, category_id, subcategory_id):
    # Запрос названия товара
    bot.send_message(message.chat.id, "Введите название товара:")
    bot.register_next_step_handler(message, collect_item_name, category_id, subcategory_id)

def collect_item_name(message, category_id, subcategory_id):
    item_name = message.text
    bot.send_message(message.chat.id, "Введите цену товара:")
    bot.register_next_step_handler(message, collect_item_price, item_name, category_id, subcategory_id)

def collect_item_price(message, item_name, category_id, subcategory_id):
    item_price = message.text
    bot.send_message(message.chat.id, "Введите описание товара:")
    bot.register_next_step_handler(message, collect_item_description, item_name, item_price, category_id, subcategory_id)

def collect_item_description(message, item_name, item_price, category_id, subcategory_id):
    item_description = message.text
    bot.send_message(message.chat.id, "Отправьте фотографии товара, если есть. Нажмите 'Описание готово' когда закончите.")
    bot.register_next_step_handler(message, collect_item_photos, item_name, item_price, item_description, category_id, subcategory_id)

def collect_item_photos(message, item_name, item_price, item_description, category_id, subcategory_id):
    # Ожидаем фотографий, пока не получим команду "Описание готово"
    if message.text == "Описание готово":
        # Отправляем товар на рассмотрение администратору
        bot.send_message(admin_chat_id, f"Новый товар на продажу: {item_name}, {item_price}₽. Описание: {item_description}")
        # Добавьте кнопки для админа: "Одобрить" и "Отклонить"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Одобрить", callback_data="approve_item"))
        markup.add(types.InlineKeyboardButton("Отклонить", callback_data="reject_item"))
        bot.send_message(admin_chat_id, "Одобрите или отклоните товар.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Жду фотографии товара или команду 'Описание готово'.")


# Обработчики для админа

# Обработчики для админа

def approve_item(call):
    try:
        # Предполагаем, что товар имеет ID, который можно извлечь из текста сообщения
        item_id = call.message.reply_to_message.text.split(":")[1].strip()  # Извлекаем ID товара
        cursor.execute("UPDATE items SET approved = 1 WHERE id = ?", (item_id,))
        conn.commit()
        bot.send_message(call.message.chat.id, "Товар одобрен!")
        bot.send_message(call.message.chat.id, "Продавцу отправлено уведомление.")
        bot.send_message(admin_chat_id, f"Товар с ID {item_id} был одобрен.")
        # Уведомляем продавца
        bot.send_message(item_id, "Ваш товар был одобрен и теперь доступен для продажи.")
    except Exception as e:
        logging.error(f"Ошибка при одобрении товара: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Попробуйте позже.")

def reject_item(call):
    try:
        item_id = call.message.reply_to_message.text.split(":")[1].strip()  # Извлекаем ID товара
        cursor.execute("UPDATE items SET approved = 0 WHERE id = ?", (item_id,))
        conn.commit()
        bot.send_message(call.message.chat.id, "Товар отклонен!")
        bot.send_message(call.message.chat.id, "Продавцу отправлено уведомление о причине отклонения.")
        bot.send_message(admin_chat_id, f"Товар с ID {item_id} был отклонен.")
        # Уведомляем продавца
        bot.send_message(item_id, "Ваш товар был отклонен. Пожалуйста, исправьте описание или фотографии и попробуйте снова.")
    except Exception as e:
        logging.error(f"Ошибка при отклонении товара: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Попробуйте позже.")
