import pandas as pd

# Загрузка исходного датасета с кодировкой Windows-1251
df = pd.read_csv('D:/Dow/100kdataset55.csv', delimiter=';')



# Инициализация DataFrames для обучающей и тестовой выборки
train_df = pd.DataFrame(columns=df.columns)
test_df = pd.DataFrame(columns=df.columns)

# Перебор категорий
for category, group in df.groupby('category'):
    if len(group) > 10:
        # Если в категории больше 10 записей, выберем 10 случайных для теста
        test_samples = group.sample(n=10, random_state=42)
        remaining_samples = group.drop(test_samples.index)
        test_df = pd.concat([test_df, test_samples])
        train_df = pd.concat([train_df, remaining_samples])
    else:
        # Если в категории 10 или меньше записей, включим их все в обучающую выборку
        train_df = pd.concat([train_df, group])

# Сброс индексов в итоговых DataFrames
train_df.reset_index(drop=True, inplace=True)
test_df.reset_index(drop=True, inplace=True)

# Сохранение в CSV с кодировкой UTF-8
train_df.to_csv('D:/Dow/100kdataset1train.csv', index=False, encoding='utf-8')
test_df.to_csv('D:/Dow/100kdataset1test.csv', index=False, encoding='utf-8')

print("Файлы train.csv и test.csv успешно созданы с кодировкой UTF-8.")
