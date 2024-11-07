import telebot
from marketplace import cursor, conn  # Импортируем уже существующий курсор и подключение

# Токен бота
TOKEN = '6294571924:AAHtYwJgGPsi5j7qTEbyWTi3qf3_d2yVVC4'

def create_bot():
    # Просто возвращаем bot, а не кортеж
    bot = telebot.TeleBot(TOKEN)
    return bot
