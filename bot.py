# -*- coding: utf-8 -*-
import os
import json
import re
from datetime import datetime
import pyowm
import random
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters



# явно указываем версию python-telegram-bot
import telegram.version
telegram.version.__version__ = '13.8'

# токен бота Telegram
bot_token = "Ваш_токен"

# URL API Telegram для получения обновлений
url = f"https://api.telegram.org/bot{bot_token}/getUpdates"


# создаем список для хранения идентификаторов чатов
saved_chat_ids = []

# если файл chat_ids.txt существует, загружаем список идентификаторов чатов из него
if os.path.exists("chat_ids.txt"):
    with open("chat_ids.txt", "r") as f:
        saved_chat_ids = [int(line.strip()) for line in f.readlines() if line.strip()]

# отправляем запрос к API Telegram
response = requests.get(url)

# извлекаем идентификаторы чатов из ответа API Telegram
data = json.loads(response.text)
for update in data["result"]:
    chat_id = update["message"]["chat"]["id"]
    if chat_id not in saved_chat_ids:
        saved_chat_ids.append(chat_id)

# сохраняем идентификаторы чатов в файл
with open("chat_ids.txt", "w") as f:
    for chat_id in saved_chat_ids:
        f.write(str(chat_id) + "\n")

#api ключ для сбора данных о погоде
owm = pyowm.OWM(api_key='Ваш API')


#список сообщений для рассылки
MESSAGES = [
    'Привет',
]

#приветственное собщение после первого диалога с ботом
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Добрый день")
    return


def send_random_message(context):
    """отправляет случайное сообщение из списка MESSAGES всем чатам, указанным в файле chat_ids.txt."""
    with open('chat_ids.txt', 'r') as f:
        chat_ids = f.read().splitlines()  # читаем все строки из файла и разбиваем на список

    message = random.choice(MESSAGES)
    for chat_id in chat_ids:
        context.bot.send_message(chat_id=chat_id, text=message)  # отправляем сообщение каждому чату


def echo(update, context):
    """отправляет случайное сообщение из списка MESSAGES в ответ на любое сообщение от пользователя."""
    message = random.choice(MESSAGES)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def send_message_at_4_30(context):
    """отправляет утреннее приветствие с текущей температурой в Самаре в градусах Цельсия всем чатам, указанным в файле chat_ids.txt."""
    owm = pyowm.OWM(api_key='Ваш API')
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place('Samara, RU')
    w = observation.weather
    temperature = w.temperature('celsius')['temp']

    message = f"Доброе утро ю ноу,сейчас за бортом 9:00 : {temperature} градусов Цельсия!"
    with open('chat_ids.txt', 'r') as f:
        chat_ids = f.read().splitlines()
    for chat_id in chat_ids:
        try:
            context.bot.send_message(chat_id=chat_id, text=message)
            print(f"Сообщение отправлено в чат {chat_id}")
        except Exception as e:
            print(f"Ошибка отправки сообщения в чат {chat_id}: {str(e)}")

updater = Updater(token='Ваш ТОКЕН:', use_context=True)

def hello(update, context):
    """отправляет приветственное сообщение и предлагает сыграть в игру камень-ножницы-бумага."""
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Давай сыграем в камень-ножницы-бумага. Напиши 'игра'.")

def game(update, context):
    """отправляет инструкцию, как выбрать ход в игре камень-ножницы-бумага."""
    if update.message.text.lower() == "игра":
        context.bot.send_message(chat_id=update.effective_chat.id, text="Выбери камень (1), ножницы (2) или бумагу (3).")
        context.user_data['game_started'] = True
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Выбери 'игра', чтобы начать игру.")

def play(update, context):
    """принимает ход игрока и выбирает случайный ход компьютера, затем определяет победителя и отправляет результат игры и предложение сыграть еще раз."""
    if not context.user_data.get("game_started"):
        context.bot.send_message(chat_id=update.effective_chat.id, text=random.choice(MESSAGES))
        return

    if not context.user_data.get("playing"):
        context.user_data["playing"] = True

    computer_choice = random.choice(['камень', 'ножницы', 'бумага'])
    player_choice = update.message.text.lower()
    if player_choice in ['1', '2', '3', 'камень', 'ножницы', 'бумага']:
        if player_choice in ['1', 'камень']:
            player_choice = 'камень'
        elif player_choice in ['2', 'ножницы']:
            player_choice = 'ножницы'
        elif player_choice in ['3', 'бумага']:
            player_choice = 'бумага'

        result = get_result(player_choice, computer_choice)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ты выбрал {player_choice}, я выбрал {computer_choice}. {result}")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Хочешь сыграть еще раз? (да/нет)")
        context.user_data["playing"] = False
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Выбери камень (1), ножницы (2) или бумагу (3).")

def repeat(update, context):
    """принимает ответ игрока на предложение сыграть еще раз и отправляет либо новую инструкцию, либо завершающее сообщение, в зависимости от ответа."""
    answer = update.message.text
    if answer.lower() in ['да', 'yes']:
        if context.user_data.get("game_started") == True:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Выбери камень (1), ножницы (2) или бумагу (3).")
            context.user_data["playing"] = False
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=random.choice(MESSAGES))
    elif answer.lower() in ['нет', 'no']:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Как скажешь!")
        context.user_data["game_started"] = False
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=random.choice(MESSAGES))


def get_result(player_choice, computer_choice):
    """определяет результат игры камень-ножницы-бумага."""
    if player_choice == computer_choice:
        return "Ничья!"
    elif player_choice == 'камень' and computer_choice == 'ножницы':
        return "Ты победил!"
    elif player_choice == 'ножницы' and computer_choice == 'бумага':
        return "Ты победил!"
    elif player_choice == 'бумага' and computer_choice == 'камень':
        return "Ты победил!"
    else:
        return "Я победил!"

def pogoda(update, context):
    """Отправляет пользователю сообщение с текущей температурой в Самаре"""
    owm = pyowm.OWM(api_key='Ваш API')
    chat_id = update.message.chat_id
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place('Samara, RU')
    w = observation.weather
    temperature = w.temperature('celsius')['temp']
    message = f"Сейчас за бортом {temperature} градусов Цельсия."
    context.bot.send_message(chat_id=chat_id, text=message)


def main():
    updater = Updater(token='Ваш ТОКЕН', use_context=True)
    dp = updater.dispatcher

 # заменяем RegexHandler на MessageHandler с фильтром Filters.regex
    pogoda_handler = MessageHandler(Filters.regex(re.compile(r'погода', re.IGNORECASE)), pogoda)

    dp.add_handler(pogoda_handler)

    # добавляем обработчик команды /start
    dp.add_handler(CommandHandler("start", start))

    # Создаем объект регулярного выражения с флагом IGNORECASE
    game_regex = re.compile(r'игра', re.IGNORECASE)

    # Добавляем обработчик для сообщений с ключевым словом "игра"
    dp.add_handler(MessageHandler(Filters.regex(game_regex), game))

    # добавляем обработчик для выбора камня, ножниц или бумаги
    dp.add_handler(MessageHandler(Filters.regex('(?i)^(камень|ножницы|бумага|1|2|3)$'), play))

    dp.add_handler(MessageHandler(Filters.regex('^(да|нет|Да|Нет|ДА|НЕТ)$'), repeat))

    # Создаем объект регулярного выражения с флагом IGNORECASE
    game_regex = re.compile(r'игра', re.IGNORECASE)

    # Добавляем обработчик для сообщений с ключевым словом "игра"
    dp.add_handler(MessageHandler(Filters.regex(game_regex), game))

    # добавляем обработчик для выбора камня, ножниц или бумаги
    dp.add_handler(MessageHandler(Filters.regex('(?i)^(камень|ножницы|бумага|1|2|3)$'), play))


    # добавляем обработчик для обработки всех сообщений
    dp.add_handler(MessageHandler(Filters.text, echo))

    job_queue = updater.job_queue

    # добавляем задачу, которая будет выполняться каждый час
    job_queue.run_repeating(send_random_message, interval=3600)

    # добавляем обработчик команды /hello
    dp.add_handler(CommandHandler("hello", hello))

    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, 4, 0, 0)
    job_queue.run_daily(send_message_at_4_30, target_time)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
