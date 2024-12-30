import pandas as pd
import ollama
import re
import os

# Загрузка данных из CSV файла
df = pd.read_csv("D:/Dow/dataset80k.csv", encoding='utf-8')

# Фильтрация по суперкатегориям с количеством продуктов меньше 400
category_counts = df['supercategory'].value_counts()
filtered_supercategories = category_counts[category_counts < 400]

# Функция для отправки запроса к модели и получения перефразированных названий для нескольких продуктов
def get_paraphrased_names(product_names):
    # Формируем список продуктов в одном запросе, без нумерации
    products_text = "\n".join([f"{name}" for name in product_names])

    print(f"Отправляем следующие названия продуктов в ламу:\n{products_text}\n")  # Печать исходных названий

    response = ollama.chat(
        model='llama3.2-vision',

        messages=[{
            'role': 'user',
            'content': f'Перефразируй сокращай следующие названия продуктов и не повторяйся! (используй синонимы, сокращай слова чтобы слова были до 4-5 букв):\n{products_text}. Ответ без добавления лишних комментариев, только перефразированные названия по одному на строку.'
        }]
    )

    # Разделяем ответ по строкам, чтобы получить список перефразированных названий
    paraphrased_names = response['message']['content'].strip().split("\n")

    # Печать полученных перефразированных названий
    print("Полученные перефразированные названия:")
    for original, paraphrased in zip(product_names, paraphrased_names):
        print(f"{original} -> {paraphrased.strip()}")

    return [name.strip() for name in paraphrased_names if name.strip()]

# Функция для обработки одной суперкатегории и сохранения в отдельный CSV файл
def process_supercategory(supercategory, df, output_dir):
    print(f"\nОбработка продуктов для суперкатегории: {supercategory}")

    # Фильтруем продукты по текущей суперкатегории
    filtered_products = df[df['supercategory'] == supercategory]

    # Определяем, сколько продуктов нужно добавить для достижения 400
    existing_product_count = len(filtered_products)
    products_to_add = 400 - existing_product_count
    print(f"Существует {existing_product_count} продуктов, необходимо добавить {products_to_add} перефразированных продуктов.")

    # Обрабатываем продукты в текущей суперкатегории группами по 5 продуктов
    added_data = []
    added_count = 0
    while added_count < products_to_add:
        # Извлекаем названия для 5 продуктов с проверкой, если продуктов меньше 5
        sample_size = min(5, products_to_add - added_count)
        product_batch = filtered_products['product'].sample(n=sample_size, replace=(sample_size > len(filtered_products))).tolist()
        category = filtered_products['category'].iloc[0]

        # Перефразируем названия продуктов
        paraphrased_names = get_paraphrased_names(product_batch)

        # Добавляем перефразированные продукты в список
        for new_product_name in paraphrased_names:
            added_data.append({
                'product': new_product_name,
                'category': category,
                'supercategory': supercategory
            })
            added_count += 1
            if added_count >= products_to_add:
                break

    # Конвертируем список добавленных данных в DataFrame и сохраняем в CSV
    new_df = pd.DataFrame(added_data)

    # Замена недопустимых символов в названии файла
    safe_supercategory = re.sub(r'[<>:"/\\|?*]', '_', supercategory)
    output_file = f"{output_dir}/{safe_supercategory}_processed_products.csv"

    new_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Перефразированные названия продуктов для суперкатегории '{supercategory}' сохранены в файл: {output_file}")

# Основная функция для обработки и сохранения каждой суперкатегории в отдельный файл
def process_and_save_supercategories(filtered_supercategories, df, output_dir, start_index=131):
    current_index = 0  # Индекс текущей суперкатегории

    for supercategory in filtered_supercategories.index:
        if current_index >= start_index:
            process_supercategory(supercategory, df, output_dir)
        current_index += 1  # Увеличиваем индекс на каждой итерации

# Указание директории для сохранения файлов и индекса для начала
output_dir = "D:/Dow/processed_supercategories"
start_index = 131  # Запуск с 126-й суперкатегории (нумерация начинается с 0)
process_and_save_supercategories(filtered_supercategories, df, output_dir, start_index)
