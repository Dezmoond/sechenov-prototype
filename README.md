Установка Требования Python 3.9 или выше Установленные зависимости в requirements.txt


https://github.com/Dezmoond/sechenov-prototype.git

cd sechenov-prototype

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python maintg.py

ссылка на модель которую нужно добавить в корневую папку  
https://drive.google.com/file/d/1a6sGK0cDlk6nGWbL_xUCeYh-QKPCZVKe/view?usp=drive_link
https://drive.google.com/file/d/1n2OONr718lQ5KLVLaBJnmcHfhleL6xDq/view?usp=drive_link

файлы из архива поместить в папку lama:
https://drive.google.com/file/d/13To9TZvuc9tuOxXgn2vqU2jrcvGlTvxg/view?usp=sharing

На сервере необходимо использование ollama server https://ollama.com/download

установка модели vision:
ollama run llama3.2-vision:11b (8gb) или ollama run llama3.2-vision:90b (55gb)
______________________________
Finetuning.py - обучение модели llama
