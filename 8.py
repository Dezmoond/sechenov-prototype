import pandas as pd
import matplotlib.pyplot as plt

# Загрузка данных из CSV файла
df = pd.read_csv("D:/Dow/dataset80k.csv")

# Вывод всех столбцов, чтобы проверить, существует ли 'supercategory'
print(df.columns)

# Фильтрация данных, исключая категорию 'несъедобное'
df_filtered = df[df['supercategory'] != 'несъедобное']

# Подсчет количества уникальных категорий
category_counts = df_filtered['supercategory'].value_counts()

# Сортировка категорий по количеству
category_counts_sorted = category_counts.sort_values(ascending=False)

# Построение круговой диаграммы
plt.figure(figsize=(8, 8))
plt.pie(category_counts_sorted, labels=category_counts_sorted.index, autopct='%1.1f%%', startangle=140)
plt.title("Распределение суперкатегорий (без 'несъедобное')")
plt.axis('equal')  # Чтобы круг был кругом
plt.show()

# Вывод списка категорий и количества их представителей
print("Список суперкатегорий и количество их представителей:")
for category, count in category_counts_sorted.items():
    print(f"Суперкатегория: {category}, Количество: {count}")





# Фильтрация суперкатегорий с количеством меньше 400
category_counts_filtered = category_counts_sorted[category_counts_sorted < 400]
# Фильтрация категорий с количеством представителей меньше 400
filtered_categories = category_counts[category_counts < 400]
# Построение круговой диаграммы для фильтрованных данных
plt.figure(figsize=(8, 8))
plt.pie(category_counts_filtered, labels=category_counts_filtered.index, autopct='%1.1f%%', startangle=140)
plt.title("Распределение суперкатегорий (с количеством меньше 400)")
plt.axis('equal')  # Чтобы круг был кругом
plt.show()

# Вывод списка суперкатегорий и их количества, если количество меньше 400
print("Список суперкатегорий с количеством представителей меньше 400:")
for category, count in category_counts_filtered.items():
    print(f"Суперкатегория меньше 400: {category}, Количество: {count}")
# Вывод количества таких категорий
print(f"Количество категорий с представителями меньше 400: {len(filtered_categories)}")

