import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import torch
from transformers import BertForSequenceClassification, BertTokenizer
import json
import ollama
import asyncio
from dotenv import load_dotenv
import os
import pytesseract
from PIL import Image
from io import BytesIO
import pandas as pd
import re
import base64
import io
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker  # Изменен импорт
from sqlalchemy.exc import IntegrityError
from datetime import datetime

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

# Установка пути к Tesseract OCR (если требуется)
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


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
def record_nutrition_request(user_id, product, calories, protein, fat, carbohydrates, category):
    session = Session()
    new_request = NutritionRequest(
        user_id=user_id,  # Сохраняем идентификатор пользователя
        product=product,
        calories=calories,
        protein=protein,
        fat=fat,
        carbohydrates=carbohydrates,
        category=category
    )
    session.add(new_request)
    session.commit()
    session.close()

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
    asyncio.run(send_nutrition_info(message.chat.id, product_name, message.from_user.id))

    # Отправляем результат пользователю
    get_nutrition(message)

async def send_nutrition_info(chat_id, product_name, user_id):
    nutrition_info = await get_nutrition_facts(product_name, user_id)
    bot.send_message(chat_id, f"ручной ввод '{product_name}':\n{nutrition_info}")

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

# Чтение CSV с категориями
category_mapping_df = pd.read_csv('category_mapping.csv')

# Создание словаря для категорий
id2label = dict(zip(category_mapping_df['Numeric Value'], category_mapping_df['Category Name']))
model_name = "model/"  # Пример, используйте вашу модель
model = BertForSequenceClassification.from_pretrained(model_name, num_labels=len(id2label))
tokenizer = BertTokenizer.from_pretrained(model_name)
model.eval()
# Определение категории товара с помощью BERT
def predict_category_with_confidence(product_name, model, tokenizer, max_length=200):
    inputs = tokenizer(
        product_name,
        max_length=max_length,
        padding='max_length',
        truncation=True,
        return_tensors="pt"
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    inputs = {key: val.to(device) for key, val in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1).squeeze()
        predicted_class = torch.argmax(probabilities).item()
        confidence = probabilities[predicted_class].item()

    # Получение метки категории по числовому значению
    predicted_label = id2label.get(predicted_class, "Неизвестно")

    return predicted_label, confidence

# Асинхронная функция для получения пищевых данных из Llama
async def get_nutrition_facts(product_name, user_id):
    print(f'необраб {product_name}')
    predicted_label, confidence = predict_category_with_confidence(product_name, model, tokenizer)
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': f'''
                    Укажите только пищевые факты для продукта '{product_name}' в формате текстовых строк. Не добавляйте никаких комментариев. 
                    Убедитесь, что каждая характеристика написана на отдельной строке апо шаблону и никак иначе. разделитель детятичных значений точка. Например:
                    - Продукт: {product_name}
                    - Калории: количество калорий
                    - Белки: количество белков (в граммах)
                    - Жиры: количество жиров (в граммах)
                    - Углеводы: количество углеводов (в граммах)
                    '''}]
    )

    # Получаем ответ в текстовом формате
    nutrition_info = response['message']['content'].replace(",", ".")

    print(nutrition_info)
    # Инициализируем значения по умолчанию
    calories = 0
    protein = 0
    fat = 0
    carbohydrates = 0

    # Обрабатываем ответ, извлекая данные
    for line in nutrition_info.splitlines():
        if 'калории' in line.lower():
            calories = extract_numeric_value(line)
        elif 'белки' in line.lower():
            protein = extract_numeric_value(line)
        elif 'жиры' in line.lower():
            fat = extract_numeric_value(line)
        elif 'углеводы' in line.lower():
            carbohydrates = extract_numeric_value(line)

    # Записываем данные в базу данных
    await record_nutrition_request(
        user_id=user_id,
        product=product_name,
        calories=float(calories),
        protein=float(protein),
        fat=float(fat),
        carbohydrates=float(carbohydrates)

    )
    print(f"Проверка значений перед записью: Калории={calories}, Белки={protein}, Жиры={fat}, Углеводы={carbohydrates}, категория={predicted_label}, уверенность = {confidence}")
    # Добавляем результат предсказания категории и уверенности в текст ответа
    nutrition_info += f"\n\nКатегория: {predicted_label}\nУверенность: {confidence}"
    return nutrition_info  # Возвращаем словарь с данными о питании


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


async def record_nutrition_request(user_id, product, calories, protein, fat, carbohydrates):
    predicted_label, confidence = predict_category_with_confidence(product, model, tokenizer)
    session = Session()  # Создаем новую сессию
    nutrition_fact = NutritionRequest(
        user_id=user_id,
        product=product,
        calories=calories,
        protein=protein,
        fat=fat,
        carbohydrates=carbohydrates,
        category=predicted_label
    )

    try:
        session.add(nutrition_fact)  # Добавляем объект в сессию
        session.commit()  # Сохраняем изменения в базе данных
    except IntegrityError as e:
        session.rollback()  # Откатываем изменения в случае ошибки
        print(f"Ошибка записи в БД: {e}")
    finally:
        session.close()  # Закрываем сессию

def image_to_base64(image, format="JPEG"):  # Изменяем формат на "JPEG"
    # Создаем объект BytesIO для хранения изображения
    buffered = io.BytesIO()
    # Сохраняем изображение в BytesIO объект в указанном формате (JPEG)
    image.save(buffered, format=format)
    # Получаем данные байтов из BytesIO объекта
    img_bytes = buffered.getvalue()
    # Кодируем байтовые данные в base64
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64
# Обработчик изображений
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file = bot.download_file(file_info.file_path)
    image = Image.open(BytesIO(file))
    base64_image = image_to_base64(image)
    # Извлечение потенциальных названий продуктов с помощью LLaMA
    asyncio.run(extract_product_names(message.chat.id, base64_image))

# Асинхронная функция для извлечения названий продуктов из распознанного текста
async def extract_product_names(chat_id, base64_image):
    response = ollama.chat(
        model="llama3.2-vision",
        messages=[{
            "role": "user",
            "content": "This image is a sales receipt. The output should be in this format - <Product name> list without numbering. Do not output anything else. Important Product maybe on Russian language. No English",
            "images": [base64_image]
        }],
    )
    # Логирование ответа для отладки
    print("Response from LLaMA:", response)  # Для отладки, можно убрать после исправления

    # Получение контента без проверки JSON
    content = response['message']['content']

    # Очищаем ответ, удаляя все символы, кроме цифр, латиницы и кириллицы
    cleaned_content = re.sub(r'[^a-zA-Zа-яА-Я0-9\s\n,]', '', content)  # Оставляем только буквы, цифры и пробелы, а также \n

    # Разделение по новой строке (\n) и удаление лишних пробелов
    products = [product.strip() for product in cleaned_content.split('\n') if product.strip()]

    # Если нет названий продуктов, отправляем сообщение об ошибке
    if not products:
        bot.send_message(chat_id, "Не удалось извлечь названия продуктов. Пожалуйста, попробуйте еще раз.")
        return

    user_selected_products[chat_id] = products
    send_product_selection(chat_id, '\n'.join(products))  # Передаем строку, разделенную \n

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

def send_product_selection(chat_id, message_content):
    # Разбиваем строку по символу новой строки
    product_names = message_content.split('\n')

    markup = InlineKeyboardMarkup()

    # Проходим по каждому товару и создаем для него кнопку
    for product_name in product_names:
        # Ограничение длины до 64 символов
        product_name = product_name[:64]

        # Убираем все неалфавитно-цифровые символы (оставляем только буквы, цифры, дефисы и подчеркивания)
        product_name_for_callback = re.sub(r'[^a-zA-Zа-яА-Я0-9_-]', '^', product_name)

        # Формируем callback_data
        callback_data = f"get_info_{product_name_for_callback}"

        # Ограничиваем длину callback_data до 64 символов
        callback_data = callback_data[:64]

        # Создаем кнопку с названием товара
        button = InlineKeyboardButton(
            f"Получить данные: {product_name}",
            callback_data=callback_data
        )
        markup.add(button)

    # Добавляем кнопку для обработки всех товаров
    markup.add(InlineKeyboardButton("Обработать всё", callback_data="process_all"))

    # Отправка сообщения с кнопками
    bot.send_message(chat_id, "Выберите товар для получения информации:", reply_markup=markup)




# Обработчик выбора товара
@bot.callback_query_handler(func=lambda call: call.data.startswith("get_info_"))
def send_product_info(call):
    product_name = call.data.split("_", 2)[2].replace("_", " ")
    user_id = call.message.chat.id  # или получите user_id из объекта call
    asyncio.run(send_nutrition_facts_async(call.message.chat.id, product_name, user_id))

async def send_nutrition_facts_async(chat_id, product_name, user_id):
    nutrition_facts = await get_nutrition_facts(product_name, user_id)
    bot.send_message(chat_id, f"'{product_name}':\n{nutrition_facts}") #фото

# Обработчик нажатия кнопки "Обработать всё"
@bot.callback_query_handler(func=lambda call: call.data == "process_all")
def process_all_products(call):
    chat_id = call.message.chat.id
    if chat_id in user_selected_products:
        asyncio.run(send_all_products_info_async(chat_id, user_selected_products[chat_id]))
    else:
        bot.send_message(chat_id, "Нет выбранных товаров для обработки.")

async def send_all_products_info_async(chat_id, products, user_id):
    for product_name in products:
        nutrition_facts = await get_nutrition_facts(product_name, user_id)
        bot.send_message(chat_id, f"Пищевая информация для '{product_name}':\n{nutrition_facts}")

# Запуск бота
bot.polling()