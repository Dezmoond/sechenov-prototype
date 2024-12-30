import pandas as pd

# Загружаем данные из CSV
df = pd.read_csv("D:/anaconda3/UPDATEFULL - UPDATEFULLDATASET.csv")

# Преобразуем каждую строку в нужный текстовый формат
text_data = []
for _, row in df.iterrows():
    # Создаем строку с основными параметрами продукта
    row_text = f"Название продукта: {row['Product']}; Категория: {row['Category']}; "
    # Проходим по всем химическим характеристикам
    for col in df.columns[2:]:  # Пропускаем первые две колонки "Product" и "Category"
        row_text += f"{col}: {row[col]}; "

    # Добавляем строку в список
    text_data.append(row_text.strip())

# Сохраняем результат в текстовый файл
with open("prepared_data.txt", "w", encoding="utf-8") as f:
    for line in text_data:
        f.write(line + "\n")
