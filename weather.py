import ollama
import requests


def get_current_weather(city):
    api_key = '4fd407a86585750ff4ba84d96747ba40'
    base_url = "http://api.openweathermap.org/data/2.5/weather"

    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()

        # Проверка, что в ответе есть необходимые данные
        if 'main' in data and 'weather' in data:
            weather = {
                'city': data.get('name', 'Неизвестно'),
                'temperature': data['main'].get('temp', 'Нет данных'),
                'description': data['weather'][0].get('description', 'Нет данных'),
                'humidity': data['main'].get('humidity', 'Нет данных'),
                'wind_speed': data['wind'].get('speed', 'Нет данных')
            }
            return weather
        else:
            return {"error": "Ответ не содержит нужной информации о погоде."}
    else:
        return {"error": f"Не удалось получить данные о погоде. Код ошибки: {response.status_code}"}


# Используем модель и добавляем вызов функции
response = ollama.chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': f'{input("")}'}],

    tools=[{
        'type': 'function',
        'function': {
            'name': 'get_current_weather',
            'description': 'Get the current weather for a city',
            'parameters': {
                'type': 'object',
                'properties': {
                    'city': {
                        'type': 'string',
                        'description': 'The name of the city',
                    },
                },
                'required': ['city'],
            },
        },
    }],
)

# Модель должна вызвать функцию и получить погоду
for tool_call in response['message']['tool_calls']:
    if tool_call['function']['name'] == 'get_current_weather':
        city = tool_call['function']['arguments']['city']
        weather_info = get_current_weather(city)

        if "error" in weather_info:
            print(weather_info["error"])
        else:
            print(
                f"Погода в {weather_info['city']}: {weather_info['description']}, температура {weather_info['temperature']}°C, влажность {weather_info['humidity']}%, ветер {weather_info['wind_speed']} м/с.")
