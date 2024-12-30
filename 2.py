import ollama

# Получаем название продукта от пользователя


# Формируем запрос с указанием формата ответа и названия продукта
response = ollama.chat(
    model='llama3.2-vision',
    messages=[{'role': 'user', 'content': f'''
    как зовут главного героя в книге Ужас в музее?
    }}
    '''}]
)

# Печатаем ответ модели
print(response['message']['content'])
