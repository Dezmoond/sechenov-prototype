Установка Требования Python 3.9 или выше Установленные зависимости в requirements.txt


https://github.com/Dezmoond/sechenov-prototype.git

cd lama4

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python maintg.py

ссылка на модель которую нужно добавить в папку /models 
https://drive.google.com/drive/folders/1I06Mz8BPWr2i5vJrGvoBZa_H9fru_af-?usp=sharing

На сервере необходимо использование ollama server https://ollama.com/download

установка модели vision:
ollama run llama3.2-vision:11b (8gb) или ollama run llama3.2-vision:90b (55gb)
