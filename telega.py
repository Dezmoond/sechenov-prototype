import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

# Ваш токен бота
TOKEN = "7405688210:AAFa42UmredYLttDMx0z4gCBOY3PkeMb84w"
bot = telebot.TeleBot(TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # Ссылка на приложение в Google Play Market
    google_play_url = "https://play.google.com/store/apps/details?id=ru.fns.billchecker"

    # Создаем клавиатуру с кнопкой
    markup = InlineKeyboardMarkup()
    install_button = InlineKeyboardButton("Установить приложение", url=google_play_url)
    markup.add(install_button)

    # Отправляем сообщение с кнопкой
    bot.send_message(
        message.chat.id,
        "Нажмите кнопку ниже, чтобы установить приложение из Google Play:",
        reply_markup=markup
    )

# Функция для рекурсивного поиска ключа "name"
def find_names(data, names):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "name":
                names.append(value)
            else:
                find_names(value, names)
    elif isinstance(data, list):
        for item in data:
            find_names(item, names)

# Обработчик для получения JSON-файлов
@bot.message_handler(content_types=['document'])
def handle_document(message):
    file_id = message.document.file_id

    # Получаем файл
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)

    try:
        # Загружаем JSON и извлекаем все названия товаров
        data = json.loads(file.decode('utf-8'))
        names = []
        find_names(data, names)  # Рекурсивный поиск ключа "name" в JSON

        # Отправляем список названий пользователю
        if names:
            bot.send_message(message.chat.id, "Найденные названия товаров:\n" + "\n".join(names))
        else:
            bot.send_message(message.chat.id, "В файле не найдены строки с ключом 'name'.")
    except json.JSONDecodeError:
        bot.send_message(message.chat.id, "Произошла ошибка при обработке JSON-файла. Проверьте его формат.")

# Запуск бота
bot.polling()
