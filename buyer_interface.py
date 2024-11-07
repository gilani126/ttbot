from bot_init import create_bot  # Импортируем функцию для создания бота
from marketplace import cursor, conn  # Импортируем из marketplace.py
from telebot import types


bot = create_bot()  # Инициализируем бота

admin_chat_id = '6853962237'  # Замените на ID вашего администратора

# Сценарий 1: Я хочу купить

def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 Я хочу купить"))
    markup.add(types.KeyboardButton("💼 Я хочу продать"))
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

def show_categories(message):
    categories = cursor.execute("SELECT * FROM categories").fetchall()
    inline_markup = types.InlineKeyboardMarkup()
    for category in categories:
        inline_markup.add(types.InlineKeyboardButton(category[1], callback_data=f"category_{category[0]}"))
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=inline_markup)

def show_subcategories(message, category_id):
    subcategories = cursor.execute("SELECT * FROM subcategories WHERE category_id = ?", (category_id,)).fetchall()
    inline_markup = types.InlineKeyboardMarkup()
    for subcategory in subcategories:
        inline_markup.add(types.InlineKeyboardButton(subcategory[1], callback_data=f"subcategory_{subcategory[0]}"))
    bot.send_message(message.chat.id, "Выберите подкатегорию:", reply_markup=inline_markup)

def show_items(message, subcategory_id):
    items = cursor.execute("SELECT * FROM items WHERE subcategory_id = ?", (subcategory_id,)).fetchall()
    inline_markup = types.InlineKeyboardMarkup()
    for item in items:
        inline_markup.add(types.InlineKeyboardButton(f"{item[1]} - {item[3]}₽", callback_data=f"item_{item[0]}"))
    bot.send_message(message.chat.id, "Выберите товар для покупки:", reply_markup=inline_markup)

def handle_item_purchase(message, item_id):
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

def handle_payment_choice(message, item):
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

# Сценарий 2: Я хочу продать

def handle_sell(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Заполнить информацию о товаре"))
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

def handle_item_info(message):
    # Запрос данных для товара
    bot.send_message(message.chat.id, "Выберите категорию для товара.")
    show_categories(message)  # Показываем категории

def collect_item_details(message, category_id):
    # Запрос названия товара
    bot.send_message(message.chat.id, "Введите название товара:")
    bot.register_next_step_handler(message, collect_item_name, category_id)

def collect_item_name(message, category_id):
    item_name = message.text
    bot.send_message(message.chat.id, "Введите цену товара:")
    bot.register_next_step_handler(message, collect_item_price, item_name, category_id)

def collect_item_price(message, item_name, category_id):
    item_price = message.text
    bot.send_message(message.chat.id, "Введите описание товара:")
    bot.register_next_step_handler(message, collect_item_description, item_name, item_price, category_id)

def collect_item_description(message, item_name, item_price, category_id):
    item_description = message.text
    bot.send_message(message.chat.id, "Отправьте фотографии товара, если есть. Нажмите 'Описание готово' когда закончите.")
    bot.register_next_step_handler(message, collect_item_photos, item_name, item_price, item_description, category_id)

def collect_item_photos(message, item_name, item_price, item_description, category_id):
    # Ожидаем фотографий, пока не получим команду "Описание готово"
    if message.text == "Описание готово":
        # Отправляем товар на рассмотрение администратору
        bot.send_message(admin_chat_id, f"Новый товар на продажу: {item_name}, {item_price}₽. Описание: {item_description}")
        # Добавьте кнопки для админа: "Одобрить" и "Отклонить"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Одобрить", callback_data="approve_item"))
        markup.add(types.InlineKeyboardButton("Отклонить", callback_data="reject_item"))
        bot.send_message(admin_chat_id, "Одобрите или отклоните товар.", reply_markup=markup)

# Обработчики для админа
def approve_item(call):
    # Обработка одобрения товара
    bot.send_message(call.message.chat.id, "Товар одобрен!")
    bot.send_message(call.message.chat.id, "Продавцу отправлено уведомление.")
    # Отправить уведомление продавцу

def reject_item(call):
    # Обработка отклонения товара
    bot.send_message(call.message.chat.id, "Товар отклонен!")
    bot.send_message(call.message.chat.id, "Продавцу отправлено уведомление о причине отклонения.")
    # Отправить уведомление продавцу