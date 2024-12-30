import pandas as pd
import json
import math

# Загрузите CSV-файл
df = pd.read_csv('D:/Dow/encoded-Dataset_56915 _5Nov24.csv', delimiter=';')

# Поменяйте местами последние три столбца: 'info', 'subcategory', 'category', 'supercategory'
df = df[['product', 'info', 'subcategory', 'category', 'supercategory']]

# Создайте список для хранения формата JSON для каждой строки
data = []

# Пройдите по каждой строке CSV
for _, row in df.iterrows():
    # Сформируйте структуру для каждой строки, поменяв порядок столбцов
    entry = {
        "prompt": row['product'],
        "response": f"info: {row['info']}; Super: {row['supercategory']}; Middle: {row['category']}; Sub: {row['subcategory']}"
    }
    # Добавьте в список
    data.append(entry)

# Определите количество файлов по 3000 записей
num_files = math.ceil(len(data) / 3000)

# Сохраните данные в несколько TXT-файлов, по 3000 записей в каждом
for i in range(num_files):
    # Выберите текущие 3000 записей
    start = i * 3000
    end = start + 3000
    subset = data[start:end]

    # Создайте имя файла с учетом номера (например, outputdataset_1.txt, outputdataset_2.txt и т.д.)
    filename = f'D:/Dow/3001/outputdataset_{i + 1}.txt'

    # Сохраните текущий набор данных в TXT-файл в формате JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(subset, f, ensure_ascii=False, indent=2)

    print(f"Данные успешно сохранены в {filename}")
