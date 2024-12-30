import pandas as pd
import matplotlib.pyplot as plt

# Загрузка данных из CSV файла
df = pd.read_csv("D:/Dow/dataset80k.csv")

# Фильтрация данных, исключая категорию 'несъедобное'
df_filtered = df[df['supercategory'] != 'несъедобное']

# Подсчёт количества продуктов для каждой категории
category_counts = df_filtered['supercategory'].value_counts()

# Фильтрация категорий с количеством представителей меньше 400
filtered_categories = category_counts[category_counts < 400]

# Вывод количества таких категорий
print(f"Количество категорий с представителями меньше 400: {len(filtered_categories)}")

# Вывод списка этих категорий и их представителей
print("Список категорий с количеством представителей меньше 400:")
for category, count in filtered_categories.items():
    print(f"Категория: {category}, Количество представителей: {count}")
