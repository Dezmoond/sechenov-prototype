import pandas as pd
import json

# Загрузите CSV-файл
df = pd.read_csv('D:/Dow/encoded-Dataset_56915 _5Nov24.csv', delimiter=';')

# Создайте список для хранения формата JSON для каждой строки
data = []

# Пройдите по каждой строке CSV
for _, row in df.iterrows():
    # Сформируйте структуру для каждой строки
    entry = {
        "prompt": row['product'],
        "response": f"info: {row['info']}; subcategory: {row['subcategory']}; category: {row['category']}; supercategory: {row['supercategory']}"
    }
    # Добавьте в список
    data.append(entry)

# Сохраните данные в TXT-файл в формате JSON
with open('D:/Dow/newdataset80llama.txt', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Данные успешно сохранены в output.txt")
