import telebot
# Токен бота
TOKEN = '6294571924:AAEwzPbLh2pluT_a4trTHWQmuxaJJTsDCpo'

def create_bot():
    # Просто возвращаем bot, а не кортеж
    bot = telebot.TeleBot(TOKEN)
    return bot

