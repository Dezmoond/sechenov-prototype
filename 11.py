import pandas as pd

# Загрузка исходного CSV файла с кодировкой Windows-1251
df = pd.read_csv('D:/Dow/100kdataset2.csv', encoding='windows-1251')

# Удаление точек с запятой в конце строк
df = df.applymap(lambda x: str(x).rstrip(';') if isinstance(x, str) else x)

# Сохранение обработанного файла в формате CSV с кодировкой UTF-8
df.to_csv('D:/Dow/100kdataset4.csv', index=False, encoding='utf-8')

print("Файл сохранен без точек с запятой в конце строк.")