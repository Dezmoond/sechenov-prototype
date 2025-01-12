import torch
import re
import json
from transformers import PreTrainedTokenizerFast, AutoModelForCausalLM
from jiwer import wer

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Using device:', device)

# Путь к моделимими
model_path = "E:/KPI/1LAMA1/lama10"

# Загрузка токенизатора и модели
tokenizer = PreTrainedTokenizerFast.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path).to(device)

# Проверка типа pad_token_id и исправление, если это список
print(f"pad_token_id type: {type(model.config.pad_token_id)}")
print(f"pad_token_id value: {model.config.pad_token_id}")

if isinstance(model.config.pad_token_id, list):
    model.config.pad_token_id = model.config.pad_token_id[0]
    print(f"pad_token_id was a list, now set to: {model.config.pad_token_id}")

# Установка pad_token_id, если оно не задано
if model.config.pad_token_id is None:
    model.config.pad_token_id = model.config.eos_token_id[0] if isinstance(model.config.eos_token_id,
                                                                           list) else model.config.eos_token_id
    print(f"pad_token_id was not set, set to eos_token_id: {model.config.pad_token_id}")


# Функция для замены нижнего подчеркивания на пробел
def replace_underscore_with_space(text):
    return text.replace('_', ' ')


# Функция для извлечения значений по ключевым словам с использованием регулярных выражений
def extract_values_after_keyword(response_text, keyword):
    pattern = rf"{keyword}:\s*([\w\s_]+)"
    matches = re.findall(pattern, response_text)
    return matches[0] if matches else None


# Функция для генерации ответа с шаблоном
def generate_response(input_text):
    system_prompt = (
        'Вы торговый эксперт, классифицирующий товары по иерархии категорий, при определении особое внимание уделяй первому слову названия товара. Первое слово зачастую подсказка  к категории. отвечаете строго по формату: supercategory: <super>; middlecategory: <middle>; subcategory: <sub>.'
    )
    prompt = f"{system_prompt}\nВопрос: {input_text}\nОтвет:"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    # Генерация ответа на основе текущего контекста
    output = model.generate(
        **inputs,
        max_length=500,
        num_return_sequences=1,
        do_sample=True,
        top_p=0.05,
        temperature=0.1,
        top_k=10,
        pad_token_id=model.config.pad_token_id
    )

    # Декодирование и вывод сгенерированного текста
    response_text = tokenizer.decode(output[0], skip_special_tokens=True)

    # Обрезка лишнего текста (удаление всего до Super)
    response_text = re.sub(r'.*Super:', 'Super:', response_text).strip()

    # Извлекаем значения для supercategory, middlecategory и subcategory
    supercategory_value = extract_values_after_keyword(response_text, "Super")
    middlecategory_value = extract_values_after_keyword(response_text, "Middle")
    subcategory_value = extract_values_after_keyword(response_text, "Sub")

    # Заменяем подчеркивания на пробелы
    supercategory_value = replace_underscore_with_space(supercategory_value) if supercategory_value else None
    middlecategory_value = replace_underscore_with_space(middlecategory_value) if middlecategory_value else None
    subcategory_value = replace_underscore_with_space(subcategory_value) if subcategory_value else None

    # Логика для корректного использования subcategory и middlecategory
    if subcategory_value == middlecategory_value:
        subcategory_value = middlecategory_value
    elif middlecategory_value and subcategory_value and subcategory_value.startswith(middlecategory_value):
        pass  # Просто пропускаем изменение

    # Формируем отформатированный ответ
    return supercategory_value, middlecategory_value, subcategory_value


# Чтение данных из файла
with open('onlyfinal/testllama_2.txt', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Статистика по WER
total_wer = 0
category_wer = {"Super": [], "Middle": [], "Sub": []}
correct_answers = 0
total_questions = len(data)

# Обработка каждого объекта в датасете
for entry in data:
    prompt = entry["prompt"]
    expected_response = entry["response"]

    # Извлекаем значения для Super, Middle и Sub из правильного ответа
    supercategory_expected = extract_values_after_keyword(expected_response, "Super")
    middlecategory_expected = extract_values_after_keyword(expected_response, "Middle")
    subcategory_expected = extract_values_after_keyword(expected_response, "Sub")

    # Заменяем подчеркивания на пробелы в правильных ответах
    supercategory_expected = replace_underscore_with_space(supercategory_expected) if supercategory_expected else None
    middlecategory_expected = replace_underscore_with_space(middlecategory_expected) if middlecategory_expected else None
    subcategory_expected = replace_underscore_with_space(subcategory_expected) if subcategory_expected else None

    # Генерация ответа
    supercategory_generated, middlecategory_generated, subcategory_generated = generate_response(prompt)

    # Вычисление WER для каждой категории
    def safe_wer(expected, generated):
        if expected is None or generated is None:
            return 1.0  # Максимальная ошибка, если данные отсутствуют
        return wer(expected, generated)


    # Замена в основном коде:
    supercategory_wer_value = safe_wer(supercategory_expected, supercategory_generated)
    middlecategory_wer_value = safe_wer(middlecategory_expected, middlecategory_generated)
    subcategory_wer_value = safe_wer(subcategory_expected, subcategory_generated)

    category_wer["Super"].append(supercategory_wer_value)
    category_wer["Middle"].append(middlecategory_wer_value)
    category_wer["Sub"].append(subcategory_wer_value)

    # Подсчет общей WER
    total_wer += supercategory_wer_value + middlecategory_wer_value + subcategory_wer_value

    # Проверка, если все категории угаданы правильно
    if supercategory_wer_value == 0 and middlecategory_wer_value == 0 and subcategory_wer_value == 0:
        correct_answers += 1

    # Печать результатов для каждой категории
    print(f"Продукт: {prompt}")
    print(f"Ответ модели: Super: {supercategory_generated}, Middle: {middlecategory_generated}, Sub: {subcategory_generated}")
    print(f"Правильный ответ: Super: {supercategory_expected}, Middle: {middlecategory_expected}, Sub: {subcategory_expected}")
    print(f"WER для Super: {supercategory_wer_value}, WER для Middle: {middlecategory_wer_value}, WER для Sub: {subcategory_wer_value}")
    print("-" * 50)

# Статистика
average_wer = total_wer / (3 * total_questions)
category_wer_avg = {category: sum(wer_list) / len(wer_list) for category, wer_list in category_wer.items()}
accuracy = (correct_answers / total_questions) * 100

# Проценты правильных ответов для каждой категории
supercategory_accuracy = (category_wer["Super"].count(0) / total_questions) * 100
middlecategory_accuracy = (category_wer["Middle"].count(0) / total_questions) * 100
subcategory_accuracy = (category_wer["Sub"].count(0) / total_questions) * 100

# Вывод статистики WEr
print("\nСтатистика:")
print(f"Общий WER по всем категориям: {average_wer:.4f}")
for category, avg_wer in category_wer_avg.items():
    print(f"WER для категории {category}: {avg_wer:.4f}")
print(f"\nОшибочных вопросов: {total_questions - correct_answers} из {total_questions}")
print(f"Процент правильных ответов: {accuracy:.2f}%")

# Вывод процентных результатов для каждой категории
print(f"Процент правильных ответов для Super: {supercategory_accuracy:.2f}%")
print(f"Процент правильных ответов для Middle: {middlecategory_accuracy:.2f}%")
print(f"Процент правильных ответов для Sub: {subcategory_accuracy:.2f}%")

# Дополнительные метрики
print("\nДополнительные метрики:")
precision = correct_answers / total_questions
recall = correct_answers / (total_questions + sum(len(v) for v in category_wer.values()))
f1_score = 2 * (precision * recall) / (precision + recall)

print(f"Точность (Precision): {precision:.4f}")
print(f"Полнота (Recall): {recall:.4f}")
print(f"F1-мера: {f1_score:.4f}")
