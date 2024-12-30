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
    # Кнопка для отправки фотографии

    markup.add(photo_button)

    with open("image/137761-mgmu_imeni_i_m_sechenova.jpg", "rb") as image:
        bot.send_photo(message.chat.id, image)

    bot.send_message(message.chat.id, '''Здравствуйте. Я телеграм-бот по автоматизированной оценки вашего рациона питания! \n\n Вы можете добавлять продукты для оценки любым удобным способом сканируя QR-код, фотографируя чек или вводя наименование продукта вручную. Если у вас есть вопросы вы можете ознакомиться с инструкцией нажав на соответсвующую кнопку. \n\nДля повторного вызова напишите /start''', reply_markup=markup)

# Обработчик нажатия кнопок "Считать QR чека" и "Инструкция"
@bot.callback_query_handler(func=lambda call: call.data in ["read_qr", "show_instruction", "request_photo", "get_nutrition"])
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

    # Создаем кнопку "Завершить"
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

    # Получаем название продукта от пользователя
    product_name = message.text

    # Асинхронно получаем информацию о продукте
    asyncio.run(send_nutrition_info(message.chat.id, product_name))

    # Отправляем результат пользователю
    get_nutrition(message)

async def send_nutrition_info(chat_id, product_name):
    nutrition_info = await get_nutrition_facts(product_name)
    record_request_to_db(chat_id, product_name, nutrition_info)
    bot.send_message(chat_id, f"Информация по '{product_name}':\n{nutrition_info}")

def request_photo(message):
    # Инструкция для пользователя отправить медиа (фото или видео)
    bot.send_message(message.chat.id, "Пожалуйста, отправьте фото или видео чека. Нажмите на иконку скрепки и выберите нужный файл.")


def read_qr(message):
    markup = InlineKeyboardMarkup()
    install_button = InlineKeyboardButton("Для Android", url="https://play.google.com/store/apps/details?id=ru.fns.billchecker")
    install_ios_button = InlineKeyboardButton("Для iPhone", url="https://apps.apple.com/ru/app/id1169353005")
    markup.add(install_button)
    markup.add(install_ios_button)
    bot.send_message(message.chat.id, "Установите приложение ФНС РФ:", reply_markup=markup)

def show_instruction(message):
    markup = InlineKeyboardMarkup()
    install_all = InlineKeyboardButton("Считать QR чека", callback_data="read_qr")
    markup.add(install_all)
    bot.send_message(message.chat.id, '''Инструкция: \n\n В нашем телеграм-боте есть несколько способов пополнять свой рацион продуктов для получения отчета о качестве вашего питания. \n\n 1) Вы можете распознать QR-код товарного чека из магазина. для этого нужно установить приложение "ФНС проверка чека" нажав кнопку вконце инструкции. \n\n -запустив это приложение наведите камеру смартфона на QR-код товарного чека. \n - выйдет информацию по чеку. нажмите на кнопку "Действия с чеком"   ''', reply_markup=markup)
    bot.send_photo(message.chat.id, open("image/instr3.PNG", "rb"))
    bot.send_message(message.chat.id, '''Нажмите на кнопку. \n - Затем выберите "Поделиться" и укажите формат "JSON" ''')
    bot.send_photo(message.chat.id, open("image/instr1.PNG", "rb"))
    bot.send_photo(message.chat.id, open("image/instr2.PNG", "rb"))
    bot.send_message(message.chat.id, '''- Поделитесь файлом указав приложение Telegram и выбрав наш телеграм-бот в качестве получателя. \n\n 2) Пришлите фотографию чека (ВАЖНО! Названия товаров должны быть хорошо различимы) или нажмите на кнопку "Фото чека" 3) Введите название товара нажав кнопку "Ввести вручную" \n\n В случае сканирования QR или отправки фотографии нужно выбрать товар который будет использован в вашем рационе.''', reply_markup=markup)

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
    text = pytesseract.image_to_string(image, lang='rus+eng')  # Устанавливаем язык OCR

    # Приведение текста к нижнему регистру и удаление спецсимволов
    processed_text = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', text.lower())

    bot.send_message(message.chat.id, f"Распознанный текст из чека:\n{processed_text}")

    # Извлечение потенциальных названий продуктов с помощью LLaMA
    asyncio.run(extract_product_names(message.chat.id, processed_text))

# Асинхронная функция для извлечения названий продуктов из распознанного текста
async def extract_product_names(chat_id, text):
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': f'''
            Извлеките только названия продуктов из следующего текста чека учитывая, что названия могут состоять из нескольких слов и не коверкай слова но можешь исправлять опечатки:
            "{text}"

            Ответ должен быть стокой и названия продуктов должны быть через запятую. Комментарии строго запрещены, только названия товаров
            '''}]
    )

    # Логирование ответа для отладки
    print("Response from LLaMA:", response)  # Для отладки, можно убрать после исправления

    # Получение контента без проверки JSON
    content = response['message']['content']

    # Очищаем ответ, удаляя лишние фразы и символы, включая нумерацию
    cleaned_content = re.sub(r'^\d+\.\s*|\* |-\s*|[\n]+', ',', content)  # Удаляем нумерацию и другие символы

    # Разделение по запятой и удаление лишних пробелов
    products = [product.strip() for product in cleaned_content.split(',') if product.strip()]

    # Если нет названий продуктов, отправляем сообщение об ошибке
    if not products:
        bot.send_message(chat_id, "Не удалось извлечь названия продуктов. Пожалуйста, попробуйте еще раз.")
        return

    user_selected_products[chat_id] = products
    send_product_selection(chat_id, products)

def find_names(data, names):
    # Проверяем, является ли data списком
    if isinstance(data, list):
        for item in data:
            find_names(item, names)  # Рекурсивный вызов для каждого элемента списка
    elif isinstance(data, dict):
        for key, value in data.items():
            if key == 'name':  # Предполагаем, что имена продуктов находятся под ключом 'name'
                names.append(value)  # Добавляем значение имени в список
            else:
                find_names(value, names)  # Рекурсивно обрабатываем значения словаря

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

        if not names:
            bot.send_message(message.chat.id, "В файле не найдены строки с ключом 'name'.")
    except json.JSONDecodeError:
        bot.send_message(message.chat.id, "Произошла ошибка при обработке JSON-файла. Проверьте его формат.")

def send_product_selection(chat_id, names):
    markup = InlineKeyboardMarkup()
    for product_name in names:
        clean_product_name = product_name.replace(" ", "_")[:30]
        clean_product_name = ''.join(e for e in clean_product_name if e.isalnum() or e == '_')
        if len(clean_product_name) > 64:
            clean_product_name = clean_product_name[:64]
        button = InlineKeyboardButton(
            f"Получить данные: {product_name}",
            callback_data=f"get_info_{clean_product_name}"
        )
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
    bot.send_message(chat_id, f"'{product_name}':\n{nutrition_facts}")

# Обработчик нажатия кнопки "Обработать всё"
@bot.callback_query_handler(func=lambda call: call.data == "process_all")
def process_all_products(call):
    chat_id = call.message.chat.id
    if chat_id in user_selected_products:
        asyncio.run(send_all_products_info_async(chat_id, user_selected_products[chat_id]))
    else:
        bot.send_message(chat_id, "Нет выбранных товаров для обработки.")

async def send_all_products_info_async(chat_id, products):
    for product_name in products:
        nutrition_facts = await get_nutrition_facts(product_name)
        bot.send_message(chat_id, f"Пищевая информация для '{product_name}':\n{nutrition_facts}")


def record_request_to_db(user_id, product_name, nutrition_info, request_time):
    # Преобразование nutrition_info в строку JSON
    nutrition_info_str = json.dumps(nutrition_info)
    query = """
        INSERT INTO nutrition_requests (user_id, product_name, nutrition_info, request_time)
        VALUES (%s, %s, %s, %s)
    """
    with engine.connect() as connection:
        connection.execute(query, (user_id, product_name, nutrition_info_str, request_time))


# Запуск бота
bot.polling()