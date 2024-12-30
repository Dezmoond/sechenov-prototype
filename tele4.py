import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import ollama
import asyncio
from dotenv import load_dotenv
import os
import pytesseract
from PIL import Image
from io import BytesIO

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Хранение выбранных товаров для каждого пользователя
user_selected_products = {}

# Установка пути к Tesseract OCR (если требуется)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    google_play_url = "https://play.google.com/store/apps/details?id=ru.fns.billchecker"
    app_store_url = "https://apps.apple.com/ru/app/id1169353005"
    markup = InlineKeyboardMarkup()
    install_button = InlineKeyboardButton("Установить для Android", url=google_play_url)
    install_ios_button = InlineKeyboardButton("Установить для iPhone", url=app_store_url)
    markup.add(install_button)
    markup.add(install_ios_button)
    bot.send_message(message.chat.id, "Нажмите кнопку ниже, чтобы установить приложение...", reply_markup=markup)

# Функция рекурсивного поиска ключа "name" в JSON
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

# Асинхронная функция для получения пищевых данных из Llama
async def get_nutrition_facts(product_name):
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': f'''
            Укажите только пищевые факты для продукта '{product_name}' в формате JSON. 
                Не добавляйте никаких комментариев:
            {{
              "product": "{product_name}",
              "calories": "Количество калорий",
              "protein": "Количество белков (в граммах)",
              "fat": "Количество жиров (в граммах)",
              "carbohydrates": "Количество углеводов (в граммах)"
            }}
            '''}]
    )
    return response['message']['content']

# Обработчик JSON-файлов
@bot.message_handler(content_types=['document'])
def handle_document(message):
    file_id = message.document.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    try:
        data = json.loads(file.decode('utf-8'))
        names = []
        find_names(data, names)
        user_selected_products[message.chat.id] = names
        send_product_selection(message.chat.id, names)
    except json.JSONDecodeError:
        bot.send_message(message.chat.id, "Произошла ошибка при обработке JSON-файла. Проверьте его формат.")

# Обработчик изображений
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file = bot.download_file(file_info.file_path)
    image = Image.open(BytesIO(file))
    text = pytesseract.image_to_string(image, lang='rus+eng')  # Устанавливаем язык OCR
    bot.send_message(message.chat.id, f"Распознанный текст из чека:\n{text}")

# Функция для отправки кнопок выбора товаров
def send_product_selection(chat_id, names):
    markup = InlineKeyboardMarkup()
    for product_name in names:
        clean_product_name = product_name.replace(" ", "_")[:30]
        clean_product_name = ''.join(e for e in clean_product_name if e.isalnum() or e == '_')
        button = InlineKeyboardButton(f"Получить данные: {product_name}", callback_data=f"get_info_{clean_product_name}")
        markup.add(button)
    markup.add(InlineKeyboardButton("Обработать всё", callback_data="process_all"))
    bot.send_message(chat_id, "Выберите товар для получения информации:", reply_markup=markup)

# Обработчик выбора товара
@bot.callback_query_handler(func=lambda call: call.data.startswith("get_info_"))
def send_product_info(call):
    product_name = call.data.split("_", 2)[2].replace("_", " ")
    asyncio.run(send_nutrition_facts_async(call.message.chat.id, product_name))

async def send_nutrition_facts_async(chat_id, product_name):
    nutrition_facts = await get_nutrition_facts(product_name)
    bot.send_message(chat_id, f"Пищевая информация для '{product_name}':\n{nutrition_facts}")

# Обработчик кнопки "Обработать всё"
@bot.callback_query_handler(func=lambda call: call.data == "process_all")
def process_all_products(call):
    chat_id = call.message.chat.id
    if chat_id in user_selected_products:
        asyncio.run(send_all_products_info_async(chat_id, user_selected_products[chat_id]))

async def send_all_products_info_async(chat_id, products):
    for product_name in products:
        nutrition_facts = await get_nutrition_facts(product_name)
        bot.send_message(chat_id, f"Пищевая информация для '{product_name}':\n{nutrition_facts}")

# Запуск бота
bot.polling()
