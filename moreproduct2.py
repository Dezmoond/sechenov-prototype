import pandas as pd
import ollama

# Загрузка данных из CSV файла
df = pd.read_csv("D:/Dow/dataset80k.csv", encoding='utf-8')

# Фильтрация по суперкатегориям с количеством продуктов меньше 400
category_counts = df['supercategory'].value_counts()
filtered_supercategories = category_counts[category_counts < 400]

# Функция для отправки запроса к модели и получения перефразированного названия
def get_paraphrased_name(product_name):
    print(f"Отправка в модель: {product_name}")  # Показываем входное название
    response = ollama.chat(
        model='llama3.2-vision',
        messages=[{
            'role': 'user',
            'content': f'Перефразируй это название продукта (можешь случайным образом убирать окончалия слов, чтобы слова были до 4-5 букв): {product_name}. без добавления лишних комментариев.'
        }]
    )
    new_name = response['message']['content'].strip()
    print(f"Получено от модели: {new_name}")  # Показываем выходное название
    return new_name

# Функция для обработки суперкатегорий и сохранения в CSV файл
def process_and_save_products(filtered_supercategories, df, output_file):
    # Перебираем все суперкатегории с количеством продуктов меньше 400
    for first_supercategory in filtered_supercategories.index:
        print(f"Обработка продуктов для суперкатегории: {first_supercategory}")

        # Фильтруем продукты по текущей суперкатегории
        filtered_products = df[df['supercategory'] == first_supercategory]

        # Определяем сколько продуктов нужно добавить для достижения 400
        existing_product_count = len(filtered_products)
        products_to_add = 400 - existing_product_count
        print(f"Существует {existing_product_count} продуктов, необходимо добавить {products_to_add} перефразированных продуктов.")

        # Создаем список для новых данных
        new_data = []

        # Обрабатываем продукты в текущей суперкатегории
        added_count = 0
        for _, row in filtered_products.iterrows():
            if added_count >= products_to_add:
                break

            product_name = row['product']
            category = row['category']
            supercategory = row['supercategory']

            # Перефразируем название продукта
            new_product_name = get_paraphrased_name(product_name)

            # Добавляем перефразированный продукт в новый список
            new_data.append({
                'product': new_product_name,
                'category': category,
                'supercategory': supercategory
            })

            added_count += 1

        # Конвертируем новый список в DataFrame
        new_df = pd.DataFrame(new_data)

        # Сохраняем данные в CSV файл (добавление в конец файла)
        new_df.to_csv(output_file, mode='a', index=False, encoding='utf-8-sig', header=not pd.io.common.file_exists(output_file))

    print(f"Перефразированные названия продуктов для всех суперкатегорий сохранены в новый CSV файл: {output_file}")

# Вызываем функцию для обработки и сохранения данных
output_file = "D:/Dow/processed_products_all_supercategories.csv"
process_and_save_products(filtered_supercategories, df, output_file)
