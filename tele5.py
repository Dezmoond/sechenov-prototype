import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import ollama
import asyncio
from dotenv import load_dotenv
import os
from paddleocr import PaddleOCR

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Инициализация PaddleOCR для распознавания русского и английского текста
ocr = PaddleOCR(use_angle_cls=True, lang='ru')


# Асинхронная функция для запроса данных по продукту из LLaMA
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
    return json.loads(response['message']['content'])


# Обработчик изображений
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file = bot.download_file(file_info.file_path)

    # Сохраняем изображение
    with open("image.jpg", "wb") as f:
        f.write(file)

    # Используем PaddleOCR для распознавания текста
    result = ocr.ocr("image.jpg", cls=True)
    recognized_text = " ".join([line[1][0] for line in result[0]])

    # Разделяем распознанные строки как список товаров
    products = recognized_text.splitlines()
    asyncio.run(process_products(message.chat.id, products))


# Асинхронная функция для обработки списка товаров
async def process_products(chat_id, products):
    results = []
    for product in products:
        try:
            nutrition_facts = await get_nutrition_facts(product)
            results.append(nutrition_facts)
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при обработке продукта '{product}': {e}")

    # Отправляем результат в виде JSON пользователю
    if results:
        result_json = json.dumps(results, indent=2, ensure_ascii=False)
        bot.send_message(chat_id, f"Пищевая информация по товарам:\n{result_json}")


# Запуск бота
bot.polling()
