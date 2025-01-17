import telebot
from uuid import uuid4  # для генерации уникальных идентификаторов
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telebot import TeleBot, types
import torch
import threading
import json
import ollama
import asyncio
from dotenv import load_dotenv
import os
import uuid
from PIL import Image
from io import BytesIO
import pandas as pd
import re
import csv
import base64
import time
import io
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker  # Изменен импорт
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pickle
from transformers import PreTrainedTokenizerFast, AutoModelForCausalLM

# Создаем словарь для подкатегорий
df = pd.read_csv('merged_file.csv', sep=';')

# Создадим словарь для быстрого поиска названия категории по подкатегории
subcategory_to_category = dict(zip(df['Sub'], df['Category Name']))

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Using device:', device)
# Путь к сохранённым файлам
vectorizer_path = '1eatornotv.pkl'
model_forest = '1eatormotm.pkl'
# Загрузка TfidfVectorizer
with open(vectorizer_path, 'rb') as file:
    loaded_vectorizer = pickle.load(file)

# Загрузка модели
with open(model_forest, 'rb') as file:
    loaded_model = pickle.load(file)
# Путь к модели
model_path = "lama"

# Загрузка токенизатора и модели
tokenizer = PreTrainedTokenizerFast.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path).to(device)

# Проверка типа pad_token_id и исправление, если это список
print(f"pad_token_id type: {type(model.config.pad_token_id)}")
print(f"pad_token_id value: {model.config.pad_token_id}")

if isinstance(model.config.pad_token_id, list):
    model.config.pad_token_id = model.config.pad_token_id[0]
    print(f"pad_token_id was a list, now set to: {model.config.pad_token_id}")

# Установка pad_token_id, если оно не задано
if model.config.pad_token_id is None:
    model.config.pad_token_id = model.config.eos_token_id[0] if isinstance(model.config.eos_token_id,
                                                                           list) else model.config.eos_token_id
    print(f"pad_token_id was not set, set to eos_token_id: {model.config.pad_token_id}")


# Определяем базовый класс
Base = declarative_base()

engine = create_engine('postgresql://dezmoond:3621393258lL@localhost/sechenov')
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Загрузка модели и токенайзера BERT



# Хранение выбранных товаров для каждого пользователя
user_selected_products = {}

class NutritionRequest(Base):
    __tablename__ = 'nutrition_requests'

    id = Column(Integer, primary_key=True)
    user_id = Column(String)  # Добавляем поле для идентификатора пользователя чата
    product = Column(String)
    calories = Column(String)
    protein = Column(String)
    fat = Column(String)
    carbohydrates = Column(String)
    request_time = Column(DateTime, default=datetime.utcnow)
    category = Column(String)

# Функция для записи данных в базу данных
def record_nutrition_request(user_id, product, category):
    session = Session()
    new_request = NutritionRequest(
        user_id=user_id,  # Сохраняем идентификатор пользователя
        product=product,
        calories=0,
        protein=0,
        fat=0,
        carbohydrates=0,
        category=category
    )
    session.add(new_request)
    session.commit()
    session.close()

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    # Inline-кнопки
    inline_markup = InlineKeyboardMarkup()
    install_all = InlineKeyboardButton("Считать QR чека", callback_data="read_qr")
    instruction = InlineKeyboardButton("Инструкция", callback_data="show_instruction")
    photo_button = InlineKeyboardButton("📷 Отправить фото чека", callback_data="request_photo")
    nutrition_button = InlineKeyboardButton("🍽️ Ввести продукт вручную", callback_data="get_nutrition")
    inline_markup.add(nutrition_button)
    inline_markup.add(install_all)
    inline_markup.add(instruction)
    inline_markup.add(photo_button)

    # Reply-кнопки
    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = KeyboardButton("🔄 Начать")
    reply_markup.add(start_button)

    # Отправляем фото и сообщение
    with open("image/137761-mgmu_imeni_i_m_sechenova.jpg", "rb") as image:
        bot.send_photo(message.chat.id, image)

    bot.send_message(
        message.chat.id,
        '''Здравствуйте. Я телеграм-бот по автоматизированной оценки вашего рациона питания! \n\nВы можете добавлять продукты для оценки любым удобным способом: сканируя QR-код, фотографируя чек или вводя наименование продукта вручную. Если у вас есть вопросы, вы можете ознакомиться с инструкцией, нажав на соответствующую кнопку. \n\nДля повторного вызова напишите /start.''',
        reply_markup=inline_markup  # Inline-кнопки
    )
    bot.send_message(
        message.chat.id,
        "Вы также можете начать заново с помощью кнопки ниже.",
        reply_markup=reply_markup  # Reply-кнопка "🔄 Начать"
    )

# Обработчик для кнопки "🔄 Начать"
@bot.message_handler(func=lambda message: message.text == "🔄 Начать")
def restart_from_button(message):
    start(message)

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

# Функция для ввода информации вручную
def get_nutrition(message):
    # Заменяем кнопки на "🛑 Завершить ручной ввод"
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    finish_button = KeyboardButton("🛑 Завершить ручной ввод")
    markup.add(finish_button)

    bot.send_message(message.chat.id, "Введите название продукта:", reply_markup=markup)
    bot.register_next_step_handler(message, process_nutrition_input)

# Обработка ввода
def process_nutrition_input(message):
    if message.text == "🛑 Завершить ручной ввод":
        # Возвращаем кнопку "🔄 Начать"
        start_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        start_button = KeyboardButton("🔄 Начать")
        start_markup.add(start_button)

        bot.send_message(
            message.chat.id,
            "Процесс завершен. Если хотите, можете начать заново с /start.",
            reply_markup=start_markup
        )
        return

    # Проверяем, что сообщение не пустое
    if not message.text or message.text.strip() == "":
        bot.send_message(message.chat.id, "Вы отправили пустое сообщение. Пожалуйста, введите название продукта.")
        get_nutrition(message)
        return

    # Обрабатываем продукт
    product_name = message.text.strip()  # Убираем лишние пробелы
    try:
        asyncio.run(send_nutrition_info(message.chat.id, product_name, message.from_user.id))
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка при обработке: {e}")

    # Снова ожидаем ввод
    get_nutrition(message)



async def send_nutrition_info(chat_id, product_name, user_id):
    nutrition_info = await get_nutrition_facts(product_name, user_id)
    category_name = subcategory_to_category.get(nutrition_info[0], "Неизвестная категория")
    bot.send_message(chat_id, f"Ручной ввод '{product_name}':\n{category_name}")
    record_nutrition_request(chat_id, product_name, category_name)

# Добавление кнопки "Начать"
@bot.message_handler(commands=['start_manual'])
def start_manual(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = KeyboardButton("🔄 Начать")
    markup.add(start_button)
    bot.send_message(message.chat.id, "Нажмите 'Начать' для повторного вызова команды /start.", reply_markup=markup)

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
async def get_nutrition_facts(product_name, user_id):
    # Преобразование введённого текста в вектор
    user_vector = loaded_vectorizer.transform([product_name])

    # Предсказание категории
    predicted_category = loaded_model.predict(user_vector)[0]
    print('predicted_category',type(predicted_category))
    if predicted_category == '0':
        system_prompt = (
            'Вы торговый эксперт, классифицирующий товары по иерархии категорий, при определении особое внимание уделяй первому слову названия товара. Первое слово зачастую подсказка  к категории. Отвечаете строго по формату: supercategory: <super>; middlecategory: <middle>; subcategory: <sub>.'
        )
        prompt = f"{system_prompt}\nВопрос: {product_name}\nОтвет:"
        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        # Генерация ответа на основе текущего контекста
        output = model.generate(
            **inputs,
            max_length=500,
            num_return_sequences=1,
            do_sample=True,
            top_p=0.05,
            temperature=0.1,
            top_k=10,
            pad_token_id=model.config.pad_token_id
        )

        # Декодирование и вывод сгенерированного текста
        response_text = tokenizer.decode(output[0], skip_special_tokens=True)

        # Обрезка лишнего текста (удаление всего до Super)
        response_text = re.sub(r'.*Super:', 'Super:', response_text).strip()

        # Извлекаем значения для supercategory, middlecategory и subcategory
        supercategory_value = extract_values_after_keyword(response_text, "Super")
        middlecategory_value = extract_values_after_keyword(response_text, "Middle")
        subcategory_value = extract_values_after_keyword(response_text, "Sub")


        # Логика для корректного использования subcategory и middlecategory
        if subcategory_value == middlecategory_value:
            subcategory_value = middlecategory_value
        elif middlecategory_value and subcategory_value and subcategory_value.startswith(middlecategory_value):
            pass  # Просто пропускаем изменение
        print(subcategory_value, user_id)
    else:
        print('несъедобное', user_id)
        subcategory_value = '16_1_1'
    print(subcategory_value, user_id)
    # Формируем отформатированный ответ
    return subcategory_value, user_id

def extract_values_after_keyword(response_text, keyword):
    pattern = rf"{keyword}:\s*([\w\s_]+)"
    matches = re.findall(pattern, response_text)
    return matches[0] if matches else None
def extract_numeric_value(line):
    match = re.search(r'([-+]?\d*\.\d+|\d+)', line)
    if match:
        try:
            # Пробуем преобразовать найденное значение в float
            return float(match.group(0))
        except ValueError:
            print(f"Ошибка преобразования в float для строки: {line}")
            return 0.0  # Возвращаем 0.0 в случае ошибки
    print(f"Не удалось найти число в строке: {line}")
    return 0.0  # Возвращаем 0.0, если ничего не найдено


# Словари для хранения связи UUID с продуктами
user_selected_products_images = {}
user_selected_products_json = {}

max_buttons = 50


# Функция для преобразования изображения в base64
def image_to_base64(image, format="JPEG"):
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64


# Обработчик изображений
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file = bot.download_file(file_info.file_path)
    image = Image.open(BytesIO(file))
    base64_image = image_to_base64(image)
    asyncio.run(extract_product_names(message.chat.id, base64_image, source='image'))


# Обработчик документа JSON
@bot.message_handler(content_types=['document'])
def handle_document(message):
    file_id = message.document.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)

    try:
        data = json.loads(file.decode('utf-8'))
        names = []
        find_names(data, names)
        if not names:
            bot.send_message(message.chat.id, "В файле не найдены строки с ключом 'name'.")
            return
        send_product_selection(message.chat.id, names, source='json')
    except json.JSONDecodeError:
        bot.send_message(message.chat.id, "Ошибка при обработке JSON-файла. Проверьте его формат.")


# Асинхронная функция для извлечения названий продуктов из изображения
async def extract_product_names(chat_id, base64_image, source):
    response = ollama.chat(
        model="llama3.2-vision", #llama3.2-vision:11b или llama3.2-vision:90b
        messages=[{
            "role": "user",
            "content": "Не пиши лишнего, только названия продуктов. This image is a sales receipt. The output should be in this format - <Product name> list without numbering.",
            "images": [base64_image]
        }]
    )

    content = response['message']['content']
    cleaned_content = re.sub(r'[^a-zA-Zа-яА-Я0-9\s\n,]', '', content)
    product_list = [product.strip() for product in cleaned_content.split('\n') if product.strip()]

    if not product_list:
        bot.send_message(chat_id, "Не удалось извлечь названия продуктов. Попробуйте еще раз.")
        return

    if source == 'image':
        send_product_selection(chat_id, product_list, source)
    else:
        send_product_selection2(chat_id, product_list)


# Функция для отправки кнопок с UUID для изображения
def send_product_selection(chat_id, product_list, source):
    markup = types.InlineKeyboardMarkup(row_width=1)

    if source == 'image':
        user_selected_products_images[chat_id] = {}
    else:
        user_selected_products_json[chat_id] = {}

    for product in product_list:
        product_uuid = str(uuid.uuid4())

        if source == 'image':
            user_selected_products_images[chat_id][product_uuid] = product
        else:
            user_selected_products_json[chat_id][product_uuid] = product

        button = types.InlineKeyboardButton(text=product, callback_data=product_uuid)
        markup.add(button)

    bot.send_message(chat_id, "Выберите товар для получения информации:", reply_markup=markup)


# Функция для отправки кнопок с названием продукта
def send_product_selection2(chat_id, product_list):
    markup = types.InlineKeyboardMarkup(row_width=1)

    for product in product_list:
        callback_data = re.sub(r'[^a-zA-Zа-яА-Я0-9_]', '_', product[:64])
        button = types.InlineKeyboardButton(text=product, callback_data=callback_data)
        markup.add(button)

    bot.send_message(chat_id, "Выберите товар для получения информации:", reply_markup=markup)

# Асинхронная функция обработки выбора товара
async def handle_product_selection_async(call):
    product_uuid = call.data

    if product_uuid in user_selected_products_images.get(call.message.chat.id, {}):
        product_name = user_selected_products_images[call.message.chat.id].get(product_uuid, "Товар не найден")
    else:
        product_name = user_selected_products_json.get(call.message.chat.id, {}).get(product_uuid, "Товар не найден")

    # Получаем данные о товаре
    subcategory_value, user_id = await get_nutrition_facts(product_name, call.message.chat.id)

    # Заменяем подкатегорию на название категории
    category_name = subcategory_to_category.get(subcategory_value, "Неизвестная категория")

    # Отправляем результат пользователю
    bot.send_message(call.message.chat.id, f"Вы выбрали: {product_name}\nКатегория: {category_name}")
    record_nutrition_request(user_id, product_name, category_name)

# Обработчик callback-запроса
@bot.callback_query_handler(func=lambda call: True)
def handle_product_selection(call):
    # Создаем новый поток для запуска асинхронной функции
    thread = threading.Thread(target=asyncio.run, args=(handle_product_selection_async(call),))
    thread.start()


# Функция для извлечения названий продуктов из JSON
def find_names(data, names):
    if isinstance(data, list):
        for item in data:
            find_names(item, names)
    elif isinstance(data, dict):
        for key, value in data.items():
            if key == 'name':
                names.append(value)
            else:
                find_names(value, names)


# Запуск бота
def start_polling():
    while True:
        try:
            bot.polling(none_stop=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            time.sleep(5)  # Ждем перед повторной попыткой

if __name__ == '__main__':
    start_polling()
