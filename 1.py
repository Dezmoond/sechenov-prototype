import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json
import ollama
import asyncio
from dotenv import load_dotenv
import os
import pytesseract
from PIL import Image
from io import BytesIO
import re
import psycopg2
from datetime import datetime
from sqlalchemy import create_engine

# Создайте строку подключения
db_url = "postgresql+psycopg2://dezmoond:3621393258lL@localhost:5432/sechenov"

# Подключение к базе данных через SQLAlchemy
engine = create_engine(db_url)

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
    markup = InlineKeyboardMarkup()
    install_all = InlineKeyboardButton("Считать QR чека", callback_data="read_qr")
    instruction = InlineKeyboardButton("Инструкция", callback_data="show_instruction")
    photo_button = InlineKeyboardButton("📷 Отправить фото чека", callback_data="request_photo")
    nutrition_button = InlineKeyboardButton("🍽️ Ввести продукт вручную", callback_data="get_nutrition")
    markup.add(nutrition_button)
    markup.add(install_all)
    markup.add(instruction)
    markup.add(photo_button)

    with open("image/137761-mgmu_imeni_i_m_sechenova.jpg", "rb") as image:
        bot.send_photo(message.chat.id, image)

    bot.send_message(message.chat.id,
                     '''Здравствуйте. Я телеграм-бот по автоматизированной оценки вашего рациона питания! \n\n Вы можете добавлять продукты для оценки любым удобным способом сканируя QR-код, фотографируя чек или вводя наименование продукта вручную. Если у вас есть вопросы вы можете ознакомиться с инструкцией нажав на соответсвующую кнопку. \n\nДля повторного вызова напишите /start''',
                     reply_markup=markup)


# Обработчик нажатия кнопок "Считать QR чека" и "Инструкция"
@bot.callback_query_handler(
    func=lambda call: call.data in ["read_qr", "show_instruction", "request_photo", "get_nutrition"])
def callback_handler(call):
    if call.data == "read_qr":
        read_qr(call.message)
    elif call.data == "show_instruction":
        show_instruction(call.message)
    elif call.data == "request_photo":
        request_photo(call.message)
    elif call.data == "get_nutrition":
        get_nutrition(call.message)


# Функция для запроса информации о продукте у пользователя
def get_nutrition(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    finish_button = KeyboardButton("🛑 Завершить ручной ввод")
    markup.add(finish_button)

    # Ожидаем ввод от пользователя и переходим к следующему шагу
    bot.register_next_step_handler(message, process_nutrition_input)
    bot.send_message(message.chat.id, "Введите название продукта:", reply_markup=markup)


# Асинхронная функция для обработки ввода пользователя
def process_nutrition_input(message):
    if message.text == "🛑 Завершить ручной ввод":
        bot.send_message(message.chat.id, "Процесс завершен. Если хотите, можете начать заново с /start.")
        return

    product_name = message.text

    # Асинхронно получаем информацию о продукте
    asyncio.run(send_nutrition_info(message.chat.id, product_name))

    # Отправляем результат пользователю
    get_nutrition(message)


async def send_nutrition_info(chat_id, product_name):
    nutrition_info = await get_nutrition_facts(product_name)
    # Добавляем в БД информацию о запросе
    record_request_to_db(chat_id, product_name, nutrition_info)
    bot.send_message(chat_id, f"Информация по '{product_name}':\n{nutrition_info}")


def record_request_to_db(user_id, product_name, nutrition_info):
    # Получаем текущее время
    request_time = datetime.now()

    # Форматируем SQL-запрос
    with engine.connect() as connection:
        query = """
        INSERT INTO nutrition_requests (user_id, product_name, nutrition_info, request_time)
        VALUES (%s, %s, %s, %s)
        """
        # Выполняем запрос
        connection.execute(query, (user_id, product_name, nutrition_info, request_time))


def request_photo(message):
    bot.send_message(message.chat.id,
                     "Пожалуйста, отправьте фото или видео чека. Нажмите на иконку скрепки и выберите нужный файл.")


def read_qr(message):
    markup = InlineKeyboardMarkup()
    install_button = InlineKeyboardButton("Для Android",
                                          url="https://play.google.com/store/apps/details?id=ru.fns.billchecker")
    install_ios_button = InlineKeyboardButton("Для iPhone", url="https://apps.apple.com/ru/app/id1169353005")
    markup.add(install_button)
    markup.add(install_ios_button)
    bot.send_message(message.chat.id, "Установите приложение ФНС РФ:", reply_markup=markup)


def show_instruction(message):
    markup = InlineKeyboardMarkup()
    install_all = InlineKeyboardButton("Считать QR чека", callback_data="read_qr")
    markup.add(install_all)
    bot.send_message(message.chat.id,
                     '''Инструкция: \n\n В нашем телеграм-боте есть несколько способов пополнять свой рацион продуктов для получения отчета о качестве вашего питания. \n\n 1) Вы можете распознать QR-код товарного чека из магазина. для этого нужно установить приложение "ФНС проверка чека" нажав кнопку вконце инструкции. \n\n -запустив это приложение наведите камеру смартфона на QR-код товарного чека. \n - выйдет информацию по чеку. нажмите на кнопку "Действия с чеком"   ''',
                     reply_markup=markup)
    bot.send_photo(message.chat.id, open("image/instr3.PNG", "rb"))
    bot.send_message(message.chat.id,
                     '''Нажмите на кнопку. \n - Затем выберите "Поделиться" и укажите формат "JSON" ''')
    bot.send_photo(message.chat.id, open("image/instr1.PNG", "rb"))
    bot.send_photo(message.chat.id, open("image/instr2.PNG", "rb"))
    bot.send_message(message.chat.id,
                     '''- Поделитесь файлом указав приложение Telegram и выбрав наш телеграм-бот в качестве получателя. \n\n 2) Пришлите фотографию чека (ВАЖНО! Названия товаров должны быть хорошо различимы) или нажмите на кнопку "Фото чека" 3) Введите название товара нажав кнопку "Ввести вручную" \n\n В случае сканирования QR или отправки фотографии нужно выбрать товар который будет использован в вашем рационе.''',
                     reply_markup=markup)


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


# Обработчик изображений
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file = bot.download_file(file_info.file_path)
    image = Image.open(BytesIO(file))
    text = pytesseract.image_to_string(image, lang='rus+eng')

    processed_text = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', text.lower())

    bot.send_message(message.chat.id, f"Распознанный текст из чека:\n{processed_text}")

    asyncio.run(extract_product_names(message.chat.id, processed_text))


# Асинхронная функция для извлечения названий продуктов из распознанного текста
async def extract_product_names(chat_id, text):
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': f'''
            Извлеките только названия продуктов из следующего текста чека учитывая, что названия могут состоять из нескольких слов: \n\n {text}
            Верните их в формате JSON, как массив строк:
            []'''}]
    )

    products = json.loads(response['message']['content'])

    if isinstance(products, list):
        user_selected_products[chat_id] = products  # Сохраняем выбранные продукты для пользователя
        await handle_product_selection(chat_id, products)
    else:
        bot.send_message(chat_id, "Не удалось извлечь названия продуктов. Попробуйте еще раз.")


async def handle_product_selection(chat_id, products):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    for product in products:
        markup.add(KeyboardButton(product))

    markup.add(KeyboardButton("🛑 Завершить выбор"))

    bot.send_message(chat_id, "Выберите продукт:", reply_markup=markup)


# Обработчик нажатия на выбранный продукт
@bot.message_handler(func=lambda message: message.text not in ["🛑 Завершить выбор"])
def product_selected(message):
    product_name = message.text

    # Получаем информацию о продукте
    asyncio.run(send_nutrition_info(message.chat.id, product_name))


# Запуск бота
bot.polling(none_stop=True)
